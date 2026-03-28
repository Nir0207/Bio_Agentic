from __future__ import annotations

import polars as pl

PROTEIN_SCHEMA = {
    "id": pl.Utf8,
    "uniprot_id": pl.Utf8,
    "name": pl.Utf8,
    "organism": pl.Utf8,
    "source": pl.Utf8,
    "reviewed": pl.Boolean,
    "string_id": pl.Utf8,
    "gene_symbol": pl.Utf8,
}

PATHWAY_SCHEMA = {
    "id": pl.Utf8,
    "reactome_id": pl.Utf8,
    "name": pl.Utf8,
    "species": pl.Utf8,
    "source": pl.Utf8,
    "parent_pathway_id": pl.Utf8,
}

PUBLICATION_SCHEMA = {
    "id": pl.Utf8,
    "pmid": pl.Utf8,
    "title": pl.Utf8,
    "abstract": pl.Utf8,
    "pub_year": pl.Int64,
    "source": pl.Utf8,
}

EVIDENCE_SCHEMA = {
    "id": pl.Utf8,
    "text": pl.Utf8,
    "evidence_type": pl.Utf8,
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "publication_id": pl.Utf8,
}

RELATIONSHIP_SCHEMA = {
    "source": pl.Utf8,
    "confidence": pl.Float64,
    "dataset_version": pl.Utf8,
}

def assert_schema(df: pl.DataFrame, schema: dict[str, pl.DataType]) -> None:
    missing = [name for name in schema if name not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
