from __future__ import annotations

import pandas as pd


def ensure_semantic_aggregate_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "semantic_similarity_avg" not in frame.columns:
        frame["semantic_similarity_avg"] = 0.0
    frame["semantic_similarity_avg"] = pd.to_numeric(frame["semantic_similarity_avg"], errors="coerce").fillna(0.0)
    return frame
