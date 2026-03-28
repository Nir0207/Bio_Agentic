from __future__ import annotations

from typing import Final

FEATURE_SCHEMA_VERSION: Final[str] = "protein_target_features_v1"
DATASET_TARGET_NAME: Final[str] = "protein_target_prioritization"

SUPPORTED_MODEL_TYPES: Final[set[str]] = {
    "logistic_regression",
    "random_forest",
    "gradient_boosting",
    "xgboost",
}
SUPPORTED_TASK_TYPES: Final[set[str]] = {"classification", "regression"}
SUPPORTED_LABEL_STRATEGIES: Final[set[str]] = {"heuristic", "heuristic_score", "heuristic_binary"}

NUMERIC_BASE_FEATURES: Final[list[str]] = [
    "interaction_count",
    "pathway_count",
    "evidence_count",
    "publication_count",
    "avg_evidence_confidence",
    "max_evidence_confidence",
    "degree_centrality_like_count",
]
OPTIONAL_NUMERIC_FEATURES: Final[list[str]] = [
    "similar_to_neighbor_count",
    "avg_similarity_score",
    "semantic_similarity_avg",
]
CATEGORICAL_FEATURES: Final[list[str]] = ["community_id"]
EMBEDDING_COLUMN: Final[str] = "graph_embedding"

HEURISTIC_WEIGHT_DEFAULTS: Final[dict[str, float]] = {
    "evidence_count": 0.35,
    "avg_evidence_confidence": 0.25,
    "pathway_count": 0.15,
    "interaction_count": 0.15,
    "publication_count": 0.05,
    "max_evidence_confidence": 0.05,
}

TARGET_SCORE_PROPERTIES: Final[dict[str, str]] = {
    "score": "target_score",
    "model_name": "target_score_model_name",
    "model_version": "target_score_model_version",
    "run_id": "target_score_run_id",
    "created_at": "target_score_created_at",
}
