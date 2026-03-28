from __future__ import annotations

from pathlib import Path

import polars as pl

from graph.validate import load_validation_queries, relationship_endpoint_integrity


def _write_gold_nodes(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        [{"id": "protein:P1", "uniprot_id": "P1", "name": "p1", "organism": "Homo sapiens", "source": "UniProt", "reviewed": True}]
    ).write_parquet(base / "nodes_protein.parquet")
    pl.DataFrame(
        [{"id": "pathway:R1", "reactome_id": "R1", "name": "pw", "species": "Homo sapiens", "source": "Reactome"}]
    ).write_parquet(base / "nodes_pathway.parquet")
    pl.DataFrame(
        [{"id": "publication:1", "pmid": "1", "title": "t", "abstract": "a", "pub_year": 2020, "source": "PubMed"}]
    ).write_parquet(base / "nodes_publication.parquet")
    pl.DataFrame(
        [{"id": "evidence:1", "text": "a", "evidence_type": "abstract", "source": "PubMed", "confidence": 1.0, "publication_id": "publication:1"}]
    ).write_parquet(base / "nodes_evidence.parquet")


def test_load_validation_queries_reads_named_blocks() -> None:
    query_file = Path(__file__).resolve().parents[1] / "graph" / "cypher" / "06_validation.cypher"
    queries = load_validation_queries(query_file)

    query_names = [name for name, _ in queries]
    assert "node_counts_by_label" in query_names
    assert "duplicate_ids_by_label" in query_names
    assert "publications_with_empty_abstract" in query_names
    assert len(queries) >= 10


def test_relationship_endpoint_integrity_detects_missing_endpoints(tmp_path: Path) -> None:
    gold_dir = tmp_path / "gold"
    _write_gold_nodes(gold_dir)

    pl.DataFrame(
        [
            {
                "source_protein_id": "protein:P1",
                "target_protein_id": "protein:P2_missing",
                "source": "STRING",
                "confidence": 900.0,
                "dataset_version": "v12.0",
            }
        ]
    ).write_parquet(gold_dir / "rel_protein_interacts_with_protein.parquet")

    reports = relationship_endpoint_integrity(gold_dir)
    interacts_report = next(report for report in reports if report["relationship"] == "INTERACTS_WITH")

    assert interacts_report["missing_source_rows"] == 0
    assert interacts_report["missing_target_rows"] == 1
    assert interacts_report["missing_either_rows"] == 1
