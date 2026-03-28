from __future__ import annotations

from typing import Any

from modeling.data.feature_loader import load_protein_features


class FakeNeo4jClient:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        params = parameters or {}
        if "protein_id" in params:
            return [row for row in self.rows if row["protein_id"] == params["protein_id"]]
        skip = int(params.get("skip", 0))
        limit = int(params.get("limit", len(self.rows)))
        return self.rows[skip : skip + limit]


def test_feature_loader_chunking_and_shape() -> None:
    rows = [
        {
            "protein_id": f"P{i:05d}",
            "community_id": str(i % 3),
            "graph_embedding": [0.1 * i, 0.2 * i],
            "interaction_count": 10.0,
            "pathway_count": 5.0,
            "evidence_count": 3.0,
            "publication_count": 2.0,
            "avg_evidence_confidence": 0.7,
            "max_evidence_confidence": 0.9,
            "degree_centrality_like_count": 10.0,
            "similar_to_neighbor_count": 4.0,
            "avg_similarity_score": 0.8,
            "semantic_similarity_avg": 0.5,
        }
        for i in range(6)
    ]

    frame, summary = load_protein_features(client=FakeNeo4jClient(rows), chunk_size=2)

    assert len(frame) == 6
    assert summary.chunk_count == 3
    assert frame.iloc[0]["protein_id"] == "P00000"
    assert isinstance(frame.iloc[0]["graph_embedding"], list)


def test_feature_loader_by_id() -> None:
    rows = [
        {
            "protein_id": "P00001",
            "community_id": "1",
            "graph_embedding": [0.1, 0.2],
            "interaction_count": 1.0,
            "pathway_count": 1.0,
            "evidence_count": 1.0,
            "publication_count": 1.0,
            "avg_evidence_confidence": 0.5,
            "max_evidence_confidence": 0.7,
            "degree_centrality_like_count": 1.0,
            "similar_to_neighbor_count": 0.0,
            "avg_similarity_score": 0.0,
            "semantic_similarity_avg": 0.0,
        }
    ]

    frame, summary = load_protein_features(client=FakeNeo4jClient(rows), protein_id="P00001")

    assert len(frame) == 1
    assert summary.row_count == 1
    assert frame.iloc[0]["protein_id"] == "P00001"
