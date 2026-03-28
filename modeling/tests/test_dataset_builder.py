from __future__ import annotations

import pandas as pd

from modeling.app.config import Settings
from modeling.data.dataset_builder import _apply_label_strategy, _split_dataset


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "protein_id": [f"P{i:05d}" for i in range(20)],
            "interaction_count": [float(i + 1) for i in range(20)],
            "pathway_count": [float((i % 5) + 1) for i in range(20)],
            "evidence_count": [float((i % 7) + 1) for i in range(20)],
            "publication_count": [float((i % 4) + 1) for i in range(20)],
            "avg_evidence_confidence": [0.3 + (i % 3) * 0.1 for i in range(20)],
            "max_evidence_confidence": [0.5 + (i % 2) * 0.2 for i in range(20)],
            "graph_embedding": [[0.1, 0.2] for _ in range(20)],
            "community_id": [str(i % 2) for i in range(20)],
            "degree_centrality_like_count": [float(i + 1) for i in range(20)],
            "similar_to_neighbor_count": [0.0 for _ in range(20)],
            "avg_similarity_score": [0.0 for _ in range(20)],
            "semantic_similarity_avg": [0.0 for _ in range(20)],
        }
    )


def test_dataset_builder_heuristic_binary_labels() -> None:
    settings = Settings(_env_file=None, label_strategy="heuristic_binary", task_type="classification")
    labeled, metadata = _apply_label_strategy(_sample_frame(), settings)

    assert "heuristic_score" in labeled.columns
    assert "label" in labeled.columns
    assert set(labeled["label"].unique()).issubset({0, 1})
    assert metadata["is_heuristic"] is True


def test_dataset_split_has_all_partitions() -> None:
    settings = Settings(_env_file=None, test_size=0.2, validation_size=0.1)
    frame = _sample_frame()
    labeled, _ = _apply_label_strategy(frame, settings)
    split_frame, manifest = _split_dataset(labeled, settings)

    assert set(split_frame["split"].unique()) == {"train", "validation", "test"}
    assert manifest["counts"]["train"] > 0
    assert manifest["counts"]["validation"] > 0
    assert manifest["counts"]["test"] > 0
