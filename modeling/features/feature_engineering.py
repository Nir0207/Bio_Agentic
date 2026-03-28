from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from modeling.app.constants import (
    CATEGORICAL_FEATURES,
    EMBEDDING_COLUMN,
    FEATURE_SCHEMA_VERSION,
    NUMERIC_BASE_FEATURES,
    OPTIONAL_NUMERIC_FEATURES,
)
from modeling.features.aggregation_features import fill_missing_with_zero
from modeling.features.graph_features import ensure_graph_numeric_features, ensure_similarity_features, normalize_community_feature
from modeling.features.semantic_features import ensure_semantic_aggregate_features

logger = logging.getLogger(__name__)


@dataclass
class FeatureMatrix:
    matrix: pd.DataFrame
    feature_columns: list[str]
    feature_schema_version: str
    embedding_dim: int


def _flatten_embedding_column(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    embeddings = frame.get(EMBEDDING_COLUMN)
    if embeddings is None:
        return pd.DataFrame(index=frame.index), 0

    normalized = embeddings.apply(lambda value: value if isinstance(value, list) else [])
    max_dim = int(normalized.map(len).max() if len(normalized) else 0)

    if max_dim == 0:
        return pd.DataFrame(index=frame.index), 0

    data: dict[str, list[float]] = {}
    for idx in range(max_dim):
        col_name = f"graph_embedding_{idx}"
        data[col_name] = [float(vector[idx]) if idx < len(vector) else 0.0 for vector in normalized]

    return pd.DataFrame(data, index=frame.index), max_dim


def build_feature_matrix(
    frame: pd.DataFrame,
    expected_columns: list[str] | None = None,
) -> FeatureMatrix:
    if frame.empty:
        raise ValueError("Cannot build feature matrix from empty dataframe")

    prepared = frame.copy()
    prepared = ensure_graph_numeric_features(prepared)
    prepared = ensure_similarity_features(prepared)
    prepared = ensure_semantic_aggregate_features(prepared)
    prepared = normalize_community_feature(prepared)

    base_numeric = prepared[[*NUMERIC_BASE_FEATURES, *OPTIONAL_NUMERIC_FEATURES]].copy()
    embedding_frame, embedding_dim = _flatten_embedding_column(prepared)

    categorical = pd.get_dummies(prepared[CATEGORICAL_FEATURES], columns=CATEGORICAL_FEATURES, prefix=CATEGORICAL_FEATURES)

    matrix = pd.concat([base_numeric, embedding_frame, categorical], axis=1)
    matrix = fill_missing_with_zero(matrix)

    if expected_columns is not None:
        matrix = matrix.reindex(columns=expected_columns, fill_value=0.0)
        feature_columns = expected_columns
    else:
        feature_columns = sorted(matrix.columns.tolist())
        matrix = matrix.reindex(columns=feature_columns)

    matrix = matrix.astype(np.float64)
    preview = feature_columns[:20]
    logger.info(
        "Feature schema version=%s feature_count=%s feature_preview=%s",
        FEATURE_SCHEMA_VERSION,
        len(feature_columns),
        preview,
    )

    return FeatureMatrix(
        matrix=matrix,
        feature_columns=feature_columns,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        embedding_dim=embedding_dim,
    )


def build_training_targets(frame: pd.DataFrame) -> pd.Series:
    if "label" not in frame.columns:
        raise ValueError("Dataset must include 'label' column before training")
    return pd.to_numeric(frame["label"], errors="coerce")


def build_prediction_frame(raw_feature_rows: pd.DataFrame, expected_columns: list[str]) -> pd.DataFrame:
    feature_matrix = build_feature_matrix(raw_feature_rows, expected_columns=expected_columns)
    return feature_matrix.matrix


def summarize_feature_manifest(
    feature_matrix: FeatureMatrix,
    dataset_version: str,
) -> dict[str, Any]:
    return {
        "dataset_version": dataset_version,
        "feature_schema_version": feature_matrix.feature_schema_version,
        "feature_columns": feature_matrix.feature_columns,
        "feature_count": len(feature_matrix.feature_columns),
        "embedding_dim": feature_matrix.embedding_dim,
    }
