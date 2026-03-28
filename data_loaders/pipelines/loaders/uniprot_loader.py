from __future__ import annotations

import gzip
import logging
import re
from pathlib import Path

import polars as pl

from pipelines.transforms.ids import protein_node_id
from pipelines.transforms.schemas import PROTEIN_SCHEMA, assert_schema

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class UniProtLoader(BaseLoader):
    source_name = "uniprot"

    def load(self, force: bool = False) -> dict[str, Path]:
        raw_file = self._raw_file()
        bronze_rows = self._parse_flat_file(raw_file)
        bronze = pl.DataFrame(bronze_rows)
        assert_schema(bronze, {
            "uniprot_id": pl.Utf8,
            "name": pl.Utf8,
            "organism": pl.Utf8,
            "reviewed": pl.Boolean,
            "string_id": pl.Utf8,
            "gene_symbol": pl.Utf8,
        })
        bronze_path = self.bronze_dir / "uniprot.parquet"
        bronze.write_parquet(bronze_path)
        logger.info("Wrote %s bronze proteins to %s", bronze.height, bronze_path)

        silver = (
            bronze.lazy()
            .filter(pl.col("reviewed").fill_null(False))
            .filter(pl.col("organism").str.contains("Homo sapiens", literal=True))
            .with_columns(
                pl.col("uniprot_id").str.strip_chars(),
                pl.col("string_id").fill_null(""),
                pl.col("gene_symbol").fill_null(""),
                pl.lit("UniProt").alias("source"),
                pl.lit(True).alias("reviewed"),
                pl.col("name").fill_null(pl.col("gene_symbol")),
            )
            .with_columns(pl.col("uniprot_id").map_elements(protein_node_id, return_dtype=pl.Utf8).alias("id"))
            .unique(subset=["uniprot_id"], keep="first")
            .sort("uniprot_id")
            .limit(self.settings.max_proteins)
            .select(["id", "uniprot_id", "name", "organism", "source", "reviewed", "string_id", "gene_symbol"])
            .collect()
        )
        assert_schema(silver, PROTEIN_SCHEMA)
        proteins_path = self.silver_dir / "proteins.parquet"
        silver.write_parquet(proteins_path)
        logger.info("Wrote %s silver proteins to %s", silver.height, proteins_path)

        string_map = (
            silver.select(["uniprot_id", "string_id", "gene_symbol"])
            .filter(pl.col("string_id").str.len_chars() > 0)
            .unique(subset=["string_id"], keep="first")
        )
        string_map_path = self.silver_dir / "string_mappings.parquet"
        string_map.write_parquet(string_map_path)
        logger.info("Wrote %s STRING mappings to %s", string_map.height, string_map_path)

        return {"bronze": bronze_path, "proteins": proteins_path, "string_mappings": string_map_path}

    def _raw_file(self) -> Path:
        candidates = sorted(self.raw_dir.glob("*.tsv.gz"))
        if not candidates:
            raise FileNotFoundError(f"No UniProt raw file found in {self.raw_dir}")
        return candidates[0]

    def _parse_flat_file(self, path: Path) -> list[dict[str, object]]:
        df = pl.read_csv(path, separator="\t", infer_schema_length=1000)
        required = {"Entry", "Protein names", "Organism", "Reviewed"}
        if not required.issubset(set(df.columns)):
            raise ValueError(f"Unexpected UniProt schema in {path}: {df.columns}")

        string_column = next((col for col in df.columns if col.lower() == "string"), None)
        if string_column is None:
            string_column = next((col for col in df.columns if "xref" in col.lower() and "string" in col.lower()), None)

        rows = []
        for row in df.iter_rows(named=True):
            string_id = self._extract_string_id(row.get(string_column)) if string_column else None
            rows.append(
                {
                    "uniprot_id": row.get("Entry"),
                    "name": row.get("Protein names") or row.get("Protein name") or row.get("Entry"),
                    "organism": row.get("Organism"),
                    "reviewed": self._as_bool(row.get("Reviewed")),
                    "string_id": string_id,
                    "gene_symbol": row.get("Gene Names (primary)") or row.get("Gene names") or row.get("Gene names  (primary )"),
                }
            )
        return rows

    def _extract_string_id(self, raw_value: object) -> str | None:
        if raw_value is None:
            return None
        value = str(raw_value).strip().strip(";")
        match = re.search(r"STRING;?\s*([A-Z0-9.]+)", value)
        if match:
            return match.group(1)
        match = re.search(r"([A-Z0-9.]+)\s*;?$", value)
        return match.group(1) if match else None

    def _as_bool(self, value: object) -> bool:
        text = str(value).strip().lower()
        return text in {"true", "reviewed", "yes", "1"}
