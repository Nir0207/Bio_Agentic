from __future__ import annotations

import io
import logging
from pathlib import Path

import polars as pl
import requests

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class StringLoader(BaseLoader):
    source_name = "string"
    api_url = "https://string-db.org/api/tsv/interaction_partners"
    api_batch_size = 250
    api_partner_limit = 30
    api_max_query_proteins = 10000

    def load(self, force: bool = False) -> dict[str, Path]:
        proteins = pl.read_parquet(self.settings.silver_dir / "uniprot" / "proteins.parquet")
        mappings = proteins.select(
            pl.col("id").alias("protein_id"),
            pl.col("uniprot_id"),
            pl.col("string_id"),
        ).filter(pl.col("string_id").is_not_null() & (pl.col("string_id") != ""))

        try:
            bronze = self._read_bronze()
        except FileNotFoundError:
            logger.warning("STRING detailed file not found; falling back to STRING API (%s).", self.api_url)
            bronze = self._read_from_api(mappings)
        bronze_path = self.bronze_dir / "string_interactions.parquet"
        bronze.write_parquet(bronze_path)
        logger.info("Wrote %s bronze STRING interactions to %s", bronze.height, bronze_path)

        detailed = (
            bronze.lazy()
            if bronze.height
            else pl.DataFrame(
                schema={
                    "source_protein_id": pl.Utf8,
                    "target_protein_id": pl.Utf8,
                    "source_uniprot_id": pl.Utf8,
                    "target_uniprot_id": pl.Utf8,
                    "confidence": pl.Float64,
                    "source": pl.Utf8,
                    "dataset_version": pl.Utf8,
                }
            ).lazy()
        )
        if bronze.height:
            detailed = (
                detailed.join(mappings.lazy(), left_on="protein1", right_on="string_id", how="inner")
                .rename({"protein_id": "source_protein_id", "uniprot_id": "source_uniprot_id"})
                .join(
                    mappings.lazy().rename(
                        {"protein_id": "target_protein_id", "uniprot_id": "target_uniprot_id", "string_id": "protein2"}
                    ),
                    left_on="protein2",
                    right_on="protein2",
                    how="inner",
                )
                .with_columns(
                    pl.lit("STRING").alias("source"),
                    pl.lit("v12.0").alias("dataset_version"),
                    pl.col("combined_score").cast(pl.Float64).alias("confidence"),
                )
                .select(
                    "source_protein_id",
                    "target_protein_id",
                    "source_uniprot_id",
                    "target_uniprot_id",
                    "confidence",
                    "source",
                    "dataset_version",
                )
                .with_columns(
                    pl.when(pl.col("source_protein_id") < pl.col("target_protein_id"))
                    .then(pl.col("source_protein_id"))
                    .otherwise(pl.col("target_protein_id"))
                    .alias("_a"),
                    pl.when(pl.col("source_protein_id") < pl.col("target_protein_id"))
                    .then(pl.col("target_protein_id"))
                    .otherwise(pl.col("source_protein_id"))
                    .alias("_b"),
                )
                .group_by(["_a", "_b", "source", "dataset_version"])
                .agg(
                    pl.max("confidence").alias("confidence"),
                    pl.first("source_protein_id").alias("source_protein_id"),
                    pl.first("target_protein_id").alias("target_protein_id"),
                )
                .drop(["_a", "_b"])
                .sort(["source_protein_id", "target_protein_id"])
            )
        detailed = detailed.collect()
        detailed_path = self.silver_dir / "protein_interactions.parquet"
        detailed.write_parquet(detailed_path)
        logger.info("Wrote %s silver STRING interactions to %s", detailed.height, detailed_path)
        if detailed.height == 0:
            raise RuntimeError(
                "STRING interactions are empty. Provide raw STRING detailed file or ensure STRING API is reachable."
            )
        return {"bronze": bronze_path, "protein_interactions": detailed_path}

    def _read_bronze(self) -> pl.DataFrame:
        candidates = sorted(self.raw_dir.glob("*.protein.links.detailed*.txt.gz"))
        if not candidates:
            raise FileNotFoundError(f"No STRING detailed file found in {self.raw_dir}")
        path = candidates[0]
        df = pl.read_csv(path, separator="\t", infer_schema_length=1000)
        required = {"protein1", "protein2", "combined_score"}
        if not required.issubset(set(df.columns)):
            raise ValueError(f"Unexpected STRING schema in {path}: {df.columns}")
        df = df.select(
            pl.col("protein1").cast(pl.Utf8),
            pl.col("protein2").cast(pl.Utf8),
            pl.col("combined_score").cast(pl.Int64),
        )
        return df.filter(pl.col("combined_score") >= self.settings.string_score_threshold).unique()

    def _read_from_api(self, mappings: pl.DataFrame) -> pl.DataFrame:
        candidate_ids = (
            mappings.select("string_id")
            .drop_nulls()
            .filter(pl.col("string_id").str.starts_with("9606."))
            .unique()
            .sort("string_id")
            .get_column("string_id")
            .to_list()
        )
        if not candidate_ids:
            return pl.DataFrame(schema={"protein1": pl.Utf8, "protein2": pl.Utf8, "combined_score": pl.Int64})

        query_ids = candidate_ids[: self.api_max_query_proteins]
        retained = set(candidate_ids)
        frames: list[pl.DataFrame] = []
        session = requests.Session()
        try:
            for start in range(0, len(query_ids), self.api_batch_size):
                batch = query_ids[start : start + self.api_batch_size]
                response = session.post(
                    self.api_url,
                    data={
                        "identifiers": "\r".join(batch),
                        "species": "9606",
                        "required_score": str(self.settings.string_score_threshold),
                        "limit": str(self.api_partner_limit),
                        "caller_identity": "omics-agentic",
                    },
                    timeout=(30, 300),
                )
                response.raise_for_status()
                text = response.text.strip()
                if not text:
                    continue
                df = pl.read_csv(io.StringIO(text), separator="\t", infer_schema_length=1000)
                required = {"stringId_A", "stringId_B", "score"}
                if not required.issubset(df.columns):
                    continue
                frames.append(
                    df.select(
                        pl.col("stringId_A").alias("protein1"),
                        pl.col("stringId_B").alias("protein2"),
                        (pl.col("score").cast(pl.Float64) * 1000.0).round(0).cast(pl.Int64).alias("combined_score"),
                    )
                    .filter(pl.col("protein1").is_in(retained) & pl.col("protein2").is_in(retained))
                )
            if not frames:
                return pl.DataFrame(schema={"protein1": pl.Utf8, "protein2": pl.Utf8, "combined_score": pl.Int64})
            return pl.concat(frames, how="vertical_relaxed").unique()
        finally:
            session.close()
