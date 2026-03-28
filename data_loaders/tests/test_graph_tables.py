from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from pipelines.transforms.graph_tables import build_graph_tables

from .conftest import make_settings


EXPECTED_GOLD_SCHEMAS: dict[str, dict[str, pl.DataType]] = {
    "nodes_protein.parquet": {
        "id": pl.Utf8,
        "uniprot_id": pl.Utf8,
        "name": pl.Utf8,
        "organism": pl.Utf8,
        "source": pl.Utf8,
        "reviewed": pl.Boolean,
    },
    "nodes_pathway.parquet": {
        "id": pl.Utf8,
        "reactome_id": pl.Utf8,
        "name": pl.Utf8,
        "species": pl.Utf8,
        "source": pl.Utf8,
    },
    "nodes_publication.parquet": {
        "id": pl.Utf8,
        "pmid": pl.Utf8,
        "title": pl.Utf8,
        "abstract": pl.Utf8,
        "pub_year": pl.Int64,
        "source": pl.Utf8,
    },
    "nodes_evidence.parquet": {
        "id": pl.Utf8,
        "text": pl.Utf8,
        "evidence_type": pl.Utf8,
        "source": pl.Utf8,
        "confidence": pl.Float64,
        "publication_id": pl.Utf8,
    },
    "rel_protein_interacts_with_protein.parquet": {
        "source_protein_id": pl.Utf8,
        "target_protein_id": pl.Utf8,
        "source": pl.Utf8,
        "confidence": pl.Float64,
        "dataset_version": pl.Utf8,
    },
    "rel_protein_participates_in_pathway.parquet": {
        "protein_id": pl.Utf8,
        "pathway_id": pl.Utf8,
        "source": pl.Utf8,
        "confidence": pl.Float64,
        "dataset_version": pl.Utf8,
    },
    "rel_publication_mentions_protein.parquet": {
        "publication_id": pl.Utf8,
        "protein_id": pl.Utf8,
        "source": pl.Utf8,
        "confidence": pl.Float64,
        "dataset_version": pl.Utf8,
    },
    "rel_publication_has_evidence.parquet": {
        "publication_id": pl.Utf8,
        "evidence_id": pl.Utf8,
        "source": pl.Utf8,
        "confidence": pl.Float64,
        "dataset_version": pl.Utf8,
    },
    "rel_evidence_supports_protein.parquet": {
        "evidence_id": pl.Utf8,
        "protein_id": pl.Utf8,
        "source": pl.Utf8,
        "confidence": pl.Float64,
        "dataset_version": pl.Utf8,
    },
    "rel_pathway_parent_of_pathway.parquet": {
        "parent_pathway_id": pl.Utf8,
        "child_pathway_id": pl.Utf8,
        "source": pl.Utf8,
        "confidence": pl.Float64,
        "dataset_version": pl.Utf8,
    },
}


def _write_minimal_silver(settings) -> None:
    pl.DataFrame(
        [
            {
                "id": "protein:P04637",
                "uniprot_id": "P04637",
                "name": "p53",
                "organism": "Homo sapiens",
                "source": "UniProt",
                "reviewed": True,
            },
            {
                "id": "protein:P38398",
                "uniprot_id": "P38398",
                "name": "BRCA1",
                "organism": "Homo sapiens",
                "source": "UniProt",
                "reviewed": True,
            },
        ]
    ).write_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")

    pl.DataFrame(
        [
            {
                "id": "pathway:R-HSA-1",
                "reactome_id": "R-HSA-1",
                "name": "TP53 signaling",
                "species": "Homo sapiens",
                "source": "Reactome",
                "parent_pathway_id": None,
            }
        ]
    ).write_parquet(settings.silver_dir / "reactome" / "pathways.parquet")

    pl.DataFrame(
        [
            {
                "id": "publication:1",
                "pmid": "1",
                "title": "TP53 regulates growth",
                "abstract": "TP53 is important in cancer.",
                "pub_year": 2019,
                "source": "PubMed",
            }
        ]
    ).write_parquet(settings.silver_dir / "pubmed" / "publications.parquet")

    pl.DataFrame(
        [
            {
                "id": "evidence:1",
                "text": "TP53 is important in cancer.",
                "evidence_type": "abstract",
                "source": "PubMed",
                "confidence": 1.0,
                "publication_id": "publication:1",
            }
        ]
    ).write_parquet(settings.silver_dir / "pubmed" / "evidence.parquet")

    pl.DataFrame(
        [
            {
                "source_protein_id": "protein:P38398",
                "target_protein_id": "protein:P04637",
                "source": "STRING",
                "confidence": 800.0,
                "dataset_version": "v12.0",
            },
            {
                "source_protein_id": "protein:P04637",
                "target_protein_id": "protein:P38398",
                "source": "STRING",
                "confidence": 900.0,
                "dataset_version": "v12.0",
            },
        ]
    ).write_parquet(settings.silver_dir / "string" / "protein_interactions.parquet")

    pl.DataFrame(
        [
            {
                "protein_id": "protein:P04637",
                "pathway_id": "pathway:R-HSA-1",
                "source": "Reactome",
                "confidence": 1.0,
                "dataset_version": "current",
            },
            {
                "protein_id": "protein:P04637",
                "pathway_id": "pathway:R-HSA-1",
                "source": "Reactome",
                "confidence": 0.5,
                "dataset_version": "current",
            },
        ]
    ).write_parquet(settings.silver_dir / "reactome" / "protein_pathways.parquet")

    pl.DataFrame(
        [
            {
                "publication_id": "publication:1",
                "protein_id": "protein:P04637",
                "source": "PubMed",
                "confidence": 0.6,
                "dataset_version": "current",
            }
        ]
    ).write_parquet(settings.silver_dir / "pubmed" / "publication_mentions.parquet")

    pl.DataFrame(
        [
            {
                "publication_id": "publication:1",
                "evidence_id": "evidence:1",
                "source": "PubMed",
                "confidence": 1.0,
                "dataset_version": "current",
            }
        ]
    ).write_parquet(settings.silver_dir / "pubmed" / "publication_evidence.parquet")

    pl.DataFrame(
        [
            {
                "evidence_id": "evidence:1",
                "protein_id": "protein:P04637",
                "source": "PubMed",
                "confidence": 0.6,
                "dataset_version": "current",
            }
        ]
    ).write_parquet(settings.silver_dir / "pubmed" / "evidence_supports.parquet")

    pl.DataFrame(
        [
            {
                "parent_pathway_id": "pathway:R-HSA-1",
                "child_pathway_id": "pathway:R-HSA-1",
                "source": "Reactome",
                "confidence": 1.0,
                "dataset_version": "current",
            }
        ]
    ).write_parquet(settings.silver_dir / "reactome" / "pathway_parent.parquet")


def test_graph_table_generation_and_schemas(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    _write_minimal_silver(settings)

    outputs = build_graph_tables(settings)

    for parquet_name, expected_schema in EXPECTED_GOLD_SCHEMAS.items():
        path = settings.gold_dir / parquet_name
        assert path.exists()
        frame = pl.read_parquet(path)
        assert list(frame.columns) == list(expected_schema.keys())
        assert frame.schema == expected_schema

    assert outputs["nodes_protein"].exists()


def test_interacts_and_participates_are_deduplicated_deterministically(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    _write_minimal_silver(settings)

    build_graph_tables(settings)

    interacts = pl.read_parquet(settings.gold_dir / "rel_protein_interacts_with_protein.parquet")
    assert interacts.height == 1
    row = interacts.row(0, named=True)
    assert row["source_protein_id"] == "protein:P04637"
    assert row["target_protein_id"] == "protein:P38398"
    assert row["confidence"] == 900.0

    participates = pl.read_parquet(settings.gold_dir / "rel_protein_participates_in_pathway.parquet")
    assert participates.height == 1
    p_row = participates.row(0, named=True)
    assert p_row["confidence"] == 1.0


def test_build_graph_tables_fails_when_required_columns_are_missing(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    # Missing required protein node columns should fail loudly.
    pl.DataFrame([{"id": "protein:P04637"}]).write_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")

    with pytest.raises(ValueError, match="Missing required columns"):
        build_graph_tables(settings)


def test_relationship_rows_with_missing_endpoints_are_dropped(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    pl.DataFrame(
        [{"id": "protein:P04637", "uniprot_id": "P04637", "name": "p53", "organism": "Homo sapiens", "source": "UniProt", "reviewed": True}]
    ).write_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")
    pl.DataFrame(
        [{"id": "pathway:R-HSA-1", "reactome_id": "R-HSA-1", "name": "TP53 signaling", "species": "Homo sapiens", "source": "Reactome", "parent_pathway_id": None}]
    ).write_parquet(settings.silver_dir / "reactome" / "pathways.parquet")
    pl.DataFrame(
        [{"id": "publication:1", "pmid": "1", "title": "t", "abstract": "a", "pub_year": 2020, "source": "PubMed"}]
    ).write_parquet(settings.silver_dir / "pubmed" / "publications.parquet")
    pl.DataFrame(
        [{"id": "evidence:1", "text": "a", "evidence_type": "abstract", "source": "PubMed", "confidence": 1.0, "publication_id": "publication:1"}]
    ).write_parquet(settings.silver_dir / "pubmed" / "evidence.parquet")
    pl.DataFrame(
        [{"source_protein_id": "protein:P04637", "target_protein_id": "protein:P99999", "source": "STRING", "confidence": 800.0, "dataset_version": "v12.0"}]
    ).write_parquet(settings.silver_dir / "string" / "protein_interactions.parquet")
    pl.DataFrame(
        [{"protein_id": "protein:P04637", "pathway_id": "pathway:R-HSA-1", "source": "Reactome", "confidence": 1.0, "dataset_version": "current"}]
    ).write_parquet(settings.silver_dir / "reactome" / "protein_pathways.parquet")
    pl.DataFrame(
        [{"publication_id": "publication:1", "protein_id": "protein:P04637", "source": "PubMed", "confidence": 0.6, "dataset_version": "current"}]
    ).write_parquet(settings.silver_dir / "pubmed" / "publication_mentions.parquet")
    pl.DataFrame(
        [{"publication_id": "publication:1", "evidence_id": "evidence:1", "source": "PubMed", "confidence": 1.0, "dataset_version": "current"}]
    ).write_parquet(settings.silver_dir / "pubmed" / "publication_evidence.parquet")
    pl.DataFrame(
        [{"evidence_id": "evidence:1", "protein_id": "protein:P04637", "source": "PubMed", "confidence": 0.6, "dataset_version": "current"}]
    ).write_parquet(settings.silver_dir / "pubmed" / "evidence_supports.parquet")
    pl.DataFrame(
        [{"parent_pathway_id": "pathway:R-HSA-1", "child_pathway_id": "pathway:R-HSA-1", "source": "Reactome", "confidence": 1.0, "dataset_version": "current"}]
    ).write_parquet(settings.silver_dir / "reactome" / "pathway_parent.parquet")

    build_graph_tables(settings)

    interactions = pl.read_parquet(settings.gold_dir / "rel_protein_interacts_with_protein.parquet")
    assert interactions.height == 0
