from __future__ import annotations

import pandas as pd

from modeling.features.feature_engineering import build_feature_matrix


def test_feature_engineering_flattens_embeddings_and_encodes_community() -> None:
    frame = pd.DataFrame(
        {
            "protein_id": ["P1", "P2"],
            "interaction_count": [1.0, 2.0],
            "pathway_count": [1.0, 2.0],
            "evidence_count": [1.0, 2.0],
            "publication_count": [1.0, 2.0],
            "avg_evidence_confidence": [0.5, 0.6],
            "max_evidence_confidence": [0.7, 0.8],
            "degree_centrality_like_count": [1.0, 2.0],
            "similar_to_neighbor_count": [0.0, 1.0],
            "avg_similarity_score": [0.0, 0.2],
            "semantic_similarity_avg": [0.0, 0.3],
            "graph_embedding": [[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]],
            "community_id": ["10", "11"],
        }
    )

    matrix = build_feature_matrix(frame)

    assert matrix.embedding_dim == 3
    assert "graph_embedding_0" in matrix.feature_columns
    assert any(column.startswith("community_id_") for column in matrix.feature_columns)
    assert matrix.matrix.shape[0] == 2
