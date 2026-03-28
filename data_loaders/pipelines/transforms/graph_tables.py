from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from app.config import Settings

logger = logging.getLogger(__name__)


def _write(df: pl.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    logger.info("Wrote %s rows to %s", df.height, path)
    return path


def _read_or_empty(path: Path, schema: dict[str, pl.DataType]) -> pl.DataFrame:
    if path.exists():
        return pl.read_parquet(path)
    return pl.DataFrame(schema=schema)


def build_graph_tables(settings: Settings) -> dict[str, Path]:
    gold_dir = settings.gold_dir
    outputs: dict[str, Path] = {}

    proteins = _read_or_empty(
        settings.silver_dir / "uniprot" / "proteins.parquet",
        {"id": pl.Utf8, "uniprot_id": pl.Utf8, "name": pl.Utf8, "organism": pl.Utf8, "source": pl.Utf8, "reviewed": pl.Boolean},
    )
    pathways = _read_or_empty(
        settings.silver_dir / "reactome" / "pathways.parquet",
        {"id": pl.Utf8, "reactome_id": pl.Utf8, "name": pl.Utf8, "species": pl.Utf8, "source": pl.Utf8, "parent_pathway_id": pl.Utf8},
    )
    publications = _read_or_empty(
        settings.silver_dir / "pubmed" / "publications.parquet",
        {"id": pl.Utf8, "pmid": pl.Utf8, "title": pl.Utf8, "abstract": pl.Utf8, "pub_year": pl.Int64, "source": pl.Utf8},
    )
    evidence = _read_or_empty(
        settings.silver_dir / "pubmed" / "evidence.parquet",
        {"id": pl.Utf8, "text": pl.Utf8, "evidence_type": pl.Utf8, "source": pl.Utf8, "confidence": pl.Float64, "publication_id": pl.Utf8},
    )
    protein_edges = _read_or_empty(
        settings.silver_dir / "string" / "protein_interactions.parquet",
        {
            "source_protein_id": pl.Utf8,
            "target_protein_id": pl.Utf8,
            "source_uniprot_id": pl.Utf8,
            "target_uniprot_id": pl.Utf8,
            "confidence": pl.Float64,
            "source": pl.Utf8,
            "dataset_version": pl.Utf8,
        },
    )
    protein_pathways = _read_or_empty(
        settings.silver_dir / "reactome" / "protein_pathways.parquet",
        {"protein_id": pl.Utf8, "pathway_id": pl.Utf8, "source": pl.Utf8, "confidence": pl.Float64, "dataset_version": pl.Utf8},
    )
    publication_mentions = _read_or_empty(
        settings.silver_dir / "pubmed" / "publication_mentions.parquet",
        {"publication_id": pl.Utf8, "protein_id": pl.Utf8, "source": pl.Utf8, "confidence": pl.Float64, "dataset_version": pl.Utf8},
    )
    publication_evidence = _read_or_empty(
        settings.silver_dir / "pubmed" / "publication_evidence.parquet",
        {"publication_id": pl.Utf8, "evidence_id": pl.Utf8, "source": pl.Utf8, "confidence": pl.Float64, "dataset_version": pl.Utf8},
    )
    evidence_supports = _read_or_empty(
        settings.silver_dir / "pubmed" / "evidence_supports.parquet",
        {"evidence_id": pl.Utf8, "protein_id": pl.Utf8, "source": pl.Utf8, "confidence": pl.Float64, "dataset_version": pl.Utf8},
    )
    pathway_parent = _read_or_empty(
        settings.silver_dir / "reactome" / "pathway_parent.parquet",
        {"parent_pathway_id": pl.Utf8, "child_pathway_id": pl.Utf8, "source": pl.Utf8, "confidence": pl.Float64, "dataset_version": pl.Utf8},
    )

    outputs["nodes_protein"] = _write(proteins, gold_dir / "nodes_protein.parquet")
    outputs["nodes_pathway"] = _write(pathways, gold_dir / "nodes_pathway.parquet")
    outputs["nodes_publication"] = _write(publications, gold_dir / "nodes_publication.parquet")
    outputs["nodes_evidence"] = _write(evidence, gold_dir / "nodes_evidence.parquet")

    outputs["rel_protein_interacts_with_protein"] = _write(
        protein_edges.select(
            "source_protein_id",
            "target_protein_id",
            "source",
            "confidence",
            "dataset_version",
        ),
        gold_dir / "rel_protein_interacts_with_protein.parquet",
    )
    outputs["rel_protein_participates_in_pathway"] = _write(
        protein_pathways.select("protein_id", "pathway_id", "source", "confidence", "dataset_version"),
        gold_dir / "rel_protein_participates_in_pathway.parquet",
    )
    outputs["rel_publication_mentions_protein"] = _write(
        publication_mentions.select("publication_id", "protein_id", "source", "confidence", "dataset_version"),
        gold_dir / "rel_publication_mentions_protein.parquet",
    )
    outputs["rel_publication_has_evidence"] = _write(
        publication_evidence.select("publication_id", "evidence_id", "source", "confidence", "dataset_version"),
        gold_dir / "rel_publication_has_evidence.parquet",
    )
    outputs["rel_evidence_supports_protein"] = _write(
        evidence_supports.select("evidence_id", "protein_id", "source", "confidence", "dataset_version"),
        gold_dir / "rel_evidence_supports_protein.parquet",
    )
    outputs["rel_pathway_parent_of_pathway"] = _write(
        pathway_parent.select("parent_pathway_id", "child_pathway_id", "source", "confidence", "dataset_version"),
        gold_dir / "rel_pathway_parent_of_pathway.parquet",
    )
    return outputs
