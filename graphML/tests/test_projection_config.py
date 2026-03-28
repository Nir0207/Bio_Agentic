from __future__ import annotations

import pytest
from pydantic import ValidationError

from graphML.app.config import Settings
from graphML.projections.graph_projection import drop_graph, graph_exists, list_graph_catalog


class FakeClient:
    def __init__(self) -> None:
        self.dropped = False

    def single(self, query: str, parameters: dict | None = None) -> dict:
        params = parameters or {}
        if "gds.graph.exists" in query:
            return {"exists": not self.dropped and params.get("graphName") == "protein_pathway_graph"}
        if "gds.graph.drop" in query:
            self.dropped = True
            return {"graphName": params.get("graphName")}
        return {}

    def run(self, query: str, parameters: dict | None = None) -> list[dict]:
        return [
            {
                "graphName": "protein_pathway_graph",
                "database": "neo4j",
                "nodeCount": 12,
                "relationshipCount": 24,
                "schema": {"nodes": ["Protein", "Pathway"]},
                "creationTime": "2026-01-01T00:00:00Z",
            }
        ]


def test_settings_parses_projection_and_algorithm_csv_values() -> None:
    settings = Settings(
        _env_file=None,
        gds_node_labels="Protein,Pathway",
        gds_relationship_types="INTERACTS_WITH,PARTICIPATES_IN,PARENT_OF",
        fastrp_iteration_weights="0.0,1.0,1.0",
        knn_node_labels="Protein,Pathway",
    )

    assert settings.gds_node_labels == ["Protein", "Pathway"]
    assert settings.gds_relationship_types == ["INTERACTS_WITH", "PARTICIPATES_IN", "PARENT_OF"]
    assert settings.fastrp_iteration_weights == [0.0, 1.0, 1.0]
    assert settings.knn_node_labels == ["Protein", "Pathway"]


def test_settings_rejects_invalid_projection_mode() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, gds_projection_mode="invalid")


def test_graph_catalog_helpers_work_with_mock_client() -> None:
    client = FakeClient()

    assert graph_exists(client, "protein_pathway_graph") is True

    entries = list_graph_catalog(client)
    assert len(entries) == 1
    assert entries[0].graph_name == "protein_pathway_graph"
    assert entries[0].node_count == 12

    removed = drop_graph(client, "protein_pathway_graph")
    assert removed is True
    assert graph_exists(client, "protein_pathway_graph") is False
