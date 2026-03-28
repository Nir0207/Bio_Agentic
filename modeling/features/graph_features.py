from __future__ import annotations

import pandas as pd

from modeling.app.constants import CATEGORICAL_FEATURES, NUMERIC_BASE_FEATURES, OPTIONAL_NUMERIC_FEATURES


def ensure_graph_numeric_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in [*NUMERIC_BASE_FEATURES, *OPTIONAL_NUMERIC_FEATURES]:
        if column not in frame.columns:
            frame[column] = 0.0
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)

    # Degree-like fallback is derived from interaction counts when explicit centrality is unavailable.
    if "degree_centrality_like_count" in frame.columns:
        frame["degree_centrality_like_count"] = frame["degree_centrality_like_count"].fillna(frame["interaction_count"])

    return frame


def normalize_community_feature(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in CATEGORICAL_FEATURES:
        if column not in frame.columns:
            frame[column] = "unknown"
        frame[column] = frame[column].fillna("unknown").astype(str)
    return frame


def ensure_similarity_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in ("similar_to_neighbor_count", "avg_similarity_score"):
        if column not in frame.columns:
            frame[column] = 0.0
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return frame
