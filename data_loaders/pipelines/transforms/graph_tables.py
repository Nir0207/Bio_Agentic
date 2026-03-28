from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from app.config import Settings

logger = logging.getLogger(__name__)


NODE_PROTEIN_SCHEMA = {
    "id": pl.Utf8,
    "uniprot_id": pl.Utf8,
    "name": pl.Utf8,
    "organism": pl.Utf8,
    "source": pl.Utf8,
    "reviewed": pl.Boolean,
}
NODE_PATHWAY_SCHEMA = {
    "id": pl.Utf8,
    "reactome_id": pl.Utf8,
    "name": pl.Utf8,
    "species": pl.Utf8,
    "source": pl.Utf8,
}
NODE_PUBLICATION_SCHEMA = {
    "id": pl.Utf8,
    "pmid": pl.Utf8,
    "title": pl.Utf8,
    "abstract": pl.Utf8,
    "pub_year": pl.Int64,
    "source": pl.Utf8,
}
NODE_EVIDENCE_SCHEMA = {
    "id": pl.Utf8,
    "text": pl.Utf8,
    "evidence_type": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "publication_id": pl.Utf8,
}

REL_INTERACTS_SCHEMA = {
    "source_protein_id": pl.Utf8,
    "target_protein_id": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "dataset_version": pl.Utf8,
}
REL_PARTICIPATES_SCHEMA = {
    "protein_id": pl.Utf8,
    "pathway_id": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "dataset_version": pl.Utf8,
}
REL_MENTIONS_SCHEMA = {
    "publication_id": pl.Utf8,
    "protein_id": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "dataset_version": pl.Utf8,
}
REL_HAS_EVIDENCE_SCHEMA = {
    "publication_id": pl.Utf8,
    "evidence_id": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "dataset_version": pl.Utf8,
}
REL_SUPPORTS_SCHEMA = {
    "evidence_id": pl.Utf8,
    "protein_id": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "dataset_version": pl.Utf8,
}
REL_PARENT_OF_SCHEMA = {
    "parent_pathway_id": pl.Utf8,
    "child_pathway_id": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "dataset_version": pl.Utf8,
}


@dataclass(frozen=True)
class SourceSpec:
    path: Path
    schema: dict[str, pl.DataType]


@dataclass(frozen=True)
class OutputSpec:
    name: str
    filename: str
    schema: dict[str, pl.DataType]
    required_non_empty: tuple[str, ...]


def _read_or_empty_lazy(spec: SourceSpec) -> pl.LazyFrame:
    if not spec.path.exists():
        logger.warning("Source parquet missing, using empty frame: %s", spec.path)
        return pl.DataFrame(schema=spec.schema).lazy()
    lf = pl.scan_parquet(spec.path)
    _assert_required_columns(lf.collect_schema().names(), spec.schema.keys(), spec.path)
    return lf


def _assert_required_columns(columns: list[str], required: object, source: Path) -> None:
    required_set = set(required)
    missing = sorted(required_set.difference(columns))
    if missing:
        raise ValueError(f"Missing required columns in {source}: {missing}")


def _sanitize_string(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Utf8, strict=False).fill_null("").str.strip_chars()


def _sanitize_confidence(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Float64, strict=False).fill_null(0.0)


def _sanitize_dataset_version(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Utf8, strict=False).fill_null("unknown").str.strip_chars()


def _coerce_schema(lf: pl.LazyFrame, schema: dict[str, pl.DataType]) -> pl.LazyFrame:
    casts = [pl.col(name).cast(dtype, strict=False).alias(name) for name, dtype in schema.items()]
    return lf.select(casts)


def _retain_existing_endpoints(
    lf: pl.LazyFrame,
    source_col: str,
    target_col: str,
    source_ids: pl.LazyFrame,
    target_ids: pl.LazyFrame,
) -> pl.LazyFrame:
    return (
        lf.join(source_ids.select(pl.col("id").alias(source_col)), on=source_col, how="inner")
        .join(target_ids.select(pl.col("id").alias(target_col)), on=target_col, how="inner")
    )


def _assert_required_non_empty(df: pl.DataFrame, columns: tuple[str, ...], output_name: str) -> None:
    for column in columns:
        empty_count = df.filter(pl.col(column).is_null() | (pl.col(column) == "")).height
        if empty_count:
            raise ValueError(f"Output {output_name} has {empty_count} empty required values for column '{column}'")


def _write(df: pl.DataFrame, path: Path, output_name: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    logger.info("Wrote %s rows to %s (%s)", df.height, path, output_name)
    return path


def build_graph_tables(settings: Settings) -> dict[str, Path]:
    gold_dir = settings.gold_dir

    proteins = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "uniprot" / "proteins.parquet",
            schema={
                "id": pl.Utf8,
                "uniprot_id": pl.Utf8,
                "name": pl.Utf8,
                "organism": pl.Utf8,
                "source": pl.Utf8,
                "reviewed": pl.Boolean,
            },
        )
    )
    pathways = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "reactome" / "pathways.parquet",
            schema={
                "id": pl.Utf8,
                "reactome_id": pl.Utf8,
                "name": pl.Utf8,
                "species": pl.Utf8,
                "source": pl.Utf8,
                "parent_pathway_id": pl.Utf8,
            },
        )
    )
    publications = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "pubmed" / "publications.parquet",
            schema={
                "id": pl.Utf8,
                "pmid": pl.Utf8,
                "title": pl.Utf8,
                "abstract": pl.Utf8,
                "pub_year": pl.Int64,
                "source": pl.Utf8,
            },
        )
    )
    evidence = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "pubmed" / "evidence.parquet",
            schema={
                "id": pl.Utf8,
                "text": pl.Utf8,
                "evidence_type": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "publication_id": pl.Utf8,
            },
        )
    )
    protein_edges = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "string" / "protein_interactions.parquet",
            schema={
                "source_protein_id": pl.Utf8,
                "target_protein_id": pl.Utf8,
                "confidence": pl.Float64,
                "source": pl.Utf8,
                "dataset_version": pl.Utf8,
            },
        )
    )
    protein_pathways = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "reactome" / "protein_pathways.parquet",
            schema={
                "protein_id": pl.Utf8,
                "pathway_id": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "dataset_version": pl.Utf8,
            },
        )
    )
    publication_mentions = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "pubmed" / "publication_mentions.parquet",
            schema={
                "publication_id": pl.Utf8,
                "protein_id": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "dataset_version": pl.Utf8,
            },
        )
    )
    publication_evidence = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "pubmed" / "publication_evidence.parquet",
            schema={
                "publication_id": pl.Utf8,
                "evidence_id": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "dataset_version": pl.Utf8,
            },
        )
    )
    evidence_supports = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "pubmed" / "evidence_supports.parquet",
            schema={
                "evidence_id": pl.Utf8,
                "protein_id": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "dataset_version": pl.Utf8,
            },
        )
    )
    pathway_parent = _read_or_empty_lazy(
        SourceSpec(
            path=settings.silver_dir / "reactome" / "pathway_parent.parquet",
            schema={
                "parent_pathway_id": pl.Utf8,
                "child_pathway_id": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "dataset_version": pl.Utf8,
            },
        )
    )

    protein_ids = proteins.select(_sanitize_string("id").alias("id")).unique()
    pathway_ids = pathways.select(_sanitize_string("id").alias("id")).unique()
    publication_ids = publications.select(_sanitize_string("id").alias("id")).unique()
    evidence_ids = evidence.select(_sanitize_string("id").alias("id")).unique()

    outputs: list[tuple[OutputSpec, pl.LazyFrame]] = []

    outputs.append(
        (
            OutputSpec("nodes_protein", "nodes_protein.parquet", NODE_PROTEIN_SCHEMA, ("id", "uniprot_id")),
            proteins
            .select(
                _sanitize_string("id").alias("id"),
                _sanitize_string("uniprot_id").alias("uniprot_id"),
                _sanitize_string("name").alias("name"),
                _sanitize_string("organism").alias("organism"),
                _sanitize_string("source").alias("source"),
                pl.col("reviewed").cast(pl.Boolean, strict=False).fill_null(False).alias("reviewed"),
            )
            .unique(subset=["id"], keep="first")
            .sort("id"),
        )
    )

    outputs.append(
        (
            OutputSpec("nodes_pathway", "nodes_pathway.parquet", NODE_PATHWAY_SCHEMA, ("id", "reactome_id")),
            pathways
            .select(
                _sanitize_string("id").alias("id"),
                _sanitize_string("reactome_id").alias("reactome_id"),
                _sanitize_string("name").alias("name"),
                _sanitize_string("species").alias("species"),
                _sanitize_string("source").alias("source"),
            )
            .unique(subset=["id"], keep="first")
            .sort("id"),
        )
    )

    outputs.append(
        (
            OutputSpec("nodes_publication", "nodes_publication.parquet", NODE_PUBLICATION_SCHEMA, ("id", "pmid")),
            publications
            .select(
                _sanitize_string("id").alias("id"),
                _sanitize_string("pmid").alias("pmid"),
                _sanitize_string("title").alias("title"),
                _sanitize_string("abstract").alias("abstract"),
                pl.col("pub_year").cast(pl.Int64, strict=False).fill_null(0).alias("pub_year"),
                _sanitize_string("source").alias("source"),
            )
            .unique(subset=["id"], keep="first")
            .sort("id"),
        )
    )

    outputs.append(
        (
            OutputSpec("nodes_evidence", "nodes_evidence.parquet", NODE_EVIDENCE_SCHEMA, ("id", "publication_id")),
            evidence
            .select(
                _sanitize_string("id").alias("id"),
                _sanitize_string("text").alias("text"),
                _sanitize_string("evidence_type").alias("evidence_type"),
                _sanitize_string("source").alias("source"),
                _sanitize_confidence("confidence").alias("confidence"),
                _sanitize_string("publication_id").alias("publication_id"),
            )
            .unique(subset=["id"], keep="first")
            .sort("id"),
        )
    )

    canonical_interacts = _retain_existing_endpoints(
        protein_edges.select(
            _sanitize_string("source_protein_id").alias("source_protein_id"),
            _sanitize_string("target_protein_id").alias("target_protein_id"),
            _sanitize_string("source").alias("source"),
            _sanitize_confidence("confidence").alias("confidence"),
            _sanitize_dataset_version("dataset_version").alias("dataset_version"),
        )
        .with_columns(
            pl.when(pl.col("source_protein_id") <= pl.col("target_protein_id"))
            .then(pl.col("source_protein_id"))
            .otherwise(pl.col("target_protein_id"))
            .alias("_source_protein_id"),
            pl.when(pl.col("source_protein_id") <= pl.col("target_protein_id"))
            .then(pl.col("target_protein_id"))
            .otherwise(pl.col("source_protein_id"))
            .alias("_target_protein_id"),
        )
        .group_by(["_source_protein_id", "_target_protein_id"])
        .agg(
            pl.col("source").sort().first().alias("source"),
            pl.col("confidence").max().alias("confidence"),
            pl.col("dataset_version").sort().first().alias("dataset_version"),
        )
        .rename({"_source_protein_id": "source_protein_id", "_target_protein_id": "target_protein_id"})
        .sort(["source_protein_id", "target_protein_id"]),
        source_col="source_protein_id",
        target_col="target_protein_id",
        source_ids=protein_ids,
        target_ids=protein_ids,
    )
    outputs.append(
        (
            OutputSpec(
                "rel_protein_interacts_with_protein",
                "rel_protein_interacts_with_protein.parquet",
                REL_INTERACTS_SCHEMA,
                ("source_protein_id", "target_protein_id"),
            ),
            canonical_interacts,
        )
    )

    def _dedupe_relationship(
        lf: pl.LazyFrame,
        source_col: str,
        target_col: str,
        schema: dict[str, pl.DataType],
    ) -> pl.LazyFrame:
        return (
            lf.select(
                _sanitize_string(source_col).alias(source_col),
                _sanitize_string(target_col).alias(target_col),
                _sanitize_string("source").alias("source"),
                _sanitize_confidence("confidence").alias("confidence"),
                _sanitize_dataset_version("dataset_version").alias("dataset_version"),
            )
            .group_by([source_col, target_col])
            .agg(
                pl.col("source").sort().first().alias("source"),
                pl.col("confidence").max().alias("confidence"),
                pl.col("dataset_version").sort().first().alias("dataset_version"),
            )
            .sort([source_col, target_col])
            .pipe(_coerce_schema, schema)
        )

    outputs.extend(
        [
            (
                OutputSpec(
                    "rel_protein_participates_in_pathway",
                    "rel_protein_participates_in_pathway.parquet",
                    REL_PARTICIPATES_SCHEMA,
                    ("protein_id", "pathway_id"),
                ),
                _dedupe_relationship(
                    _retain_existing_endpoints(
                        protein_pathways,
                        source_col="protein_id",
                        target_col="pathway_id",
                        source_ids=protein_ids,
                        target_ids=pathway_ids,
                    ),
                    "protein_id",
                    "pathway_id",
                    REL_PARTICIPATES_SCHEMA,
                ),
            ),
            (
                OutputSpec(
                    "rel_publication_mentions_protein",
                    "rel_publication_mentions_protein.parquet",
                    REL_MENTIONS_SCHEMA,
                    ("publication_id", "protein_id"),
                ),
                _dedupe_relationship(
                    _retain_existing_endpoints(
                        publication_mentions,
                        source_col="publication_id",
                        target_col="protein_id",
                        source_ids=publication_ids,
                        target_ids=protein_ids,
                    ),
                    "publication_id",
                    "protein_id",
                    REL_MENTIONS_SCHEMA,
                ),
            ),
            (
                OutputSpec(
                    "rel_publication_has_evidence",
                    "rel_publication_has_evidence.parquet",
                    REL_HAS_EVIDENCE_SCHEMA,
                    ("publication_id", "evidence_id"),
                ),
                _dedupe_relationship(
                    _retain_existing_endpoints(
                        publication_evidence,
                        source_col="publication_id",
                        target_col="evidence_id",
                        source_ids=publication_ids,
                        target_ids=evidence_ids,
                    ),
                    "publication_id",
                    "evidence_id",
                    REL_HAS_EVIDENCE_SCHEMA,
                ),
            ),
            (
                OutputSpec(
                    "rel_evidence_supports_protein",
                    "rel_evidence_supports_protein.parquet",
                    REL_SUPPORTS_SCHEMA,
                    ("evidence_id", "protein_id"),
                ),
                _dedupe_relationship(
                    _retain_existing_endpoints(
                        evidence_supports,
                        source_col="evidence_id",
                        target_col="protein_id",
                        source_ids=evidence_ids,
                        target_ids=protein_ids,
                    ),
                    "evidence_id",
                    "protein_id",
                    REL_SUPPORTS_SCHEMA,
                ),
            ),
            (
                OutputSpec(
                    "rel_pathway_parent_of_pathway",
                    "rel_pathway_parent_of_pathway.parquet",
                    REL_PARENT_OF_SCHEMA,
                    ("parent_pathway_id", "child_pathway_id"),
                ),
                _dedupe_relationship(
                    _retain_existing_endpoints(
                        pathway_parent,
                        source_col="parent_pathway_id",
                        target_col="child_pathway_id",
                        source_ids=pathway_ids,
                        target_ids=pathway_ids,
                    ),
                    "parent_pathway_id",
                    "child_pathway_id",
                    REL_PARENT_OF_SCHEMA,
                ),
            ),
        ]
    )

    written: dict[str, Path] = {}
    for spec, lf in outputs:
        coerced = _coerce_schema(lf, spec.schema)
        frame = coerced.collect()
        _assert_required_non_empty(frame, spec.required_non_empty, spec.name)
        written[spec.name] = _write(frame, gold_dir / spec.filename, spec.name)

    return written
