from __future__ import annotations

from pathlib import Path

import polars as pl

from pipelines.transforms.graph_tables import build_graph_tables

from .conftest import make_settings


def test_graph_table_generation(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    pl.DataFrame(
        [{"id": "protein:P04637", "uniprot_id": "P04637", "name": "p53", "organism": "Homo sapiens", "source": "UniProt", "reviewed": True}]
    ).write_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")
    pl.DataFrame(
        [{"id": "pathway:R-HSA-1", "reactome_id": "R-HSA-1", "name": "TP53 signaling", "species": "Homo sapiens", "source": "Reactome", "parent_pathway_id": None}]
    ).write_parquet(settings.silver_dir / "reactome" / "pathways.parquet")
    pl.DataFrame(
        [{"id": "publication:1", "pmid": "1", "title": "TP53 regulates growth", "abstract": "TP53 is important in cancer.", "pub_year": 2019, "source": "PubMed"}]
    ).write_parquet(settings.silver_dir / "pubmed" / "publications.parquet")
    pl.DataFrame(
        [{"id": "evidence:1", "text": "TP53 is important in cancer.", "evidence_type": "abstract", "source": "PubMed", "confidence": 1.0, "publication_id": "publication:1"}]
    ).write_parquet(settings.silver_dir / "pubmed" / "evidence.parquet")
    pl.DataFrame(
        [{"source_protein_id": "protein:P04637", "target_protein_id": "protein:P04637", "source": "STRING", "confidence": 900.0, "dataset_version": "v12.0"}]
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

    outputs = build_graph_tables(settings)
    assert (settings.gold_dir / "nodes_protein.parquet").exists()
    assert (settings.gold_dir / "rel_publication_has_evidence.parquet").exists()
    assert outputs["nodes_protein"].exists()

