from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from modeling.app.constants import EMBEDDING_COLUMN, NUMERIC_BASE_FEATURES, OPTIONAL_NUMERIC_FEATURES
from modeling.app.neo4j_client import Neo4jClient
from modeling.data.query_templates import PROTEIN_FEATURE_ROW_BY_ID_QUERY, PROTEIN_FEATURE_ROWS_QUERY

logger = logging.getLogger(__name__)


@dataclass
class FeatureLoadSummary:
    row_count: int
    chunk_size: int
    chunk_count: int


def _normalize_embedding(raw_value: Any) -> list[float]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [float(x) for x in raw_value]
    if isinstance(raw_value, tuple):
        return [float(x) for x in list(raw_value)]
    return []


def _coerce_numeric_columns(frame: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [*NUMERIC_BASE_FEATURES, *OPTIONAL_NUMERIC_FEATURES]
    for column in numeric_columns:
        if column not in frame.columns:
            frame[column] = 0.0
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return frame


def load_protein_features(
    client: Neo4jClient,
    chunk_size: int = 25000,
    protein_id: str | None = None,
) -> tuple[pd.DataFrame, FeatureLoadSummary]:
    if protein_id:
        rows = client.run(PROTEIN_FEATURE_ROW_BY_ID_QUERY, {"protein_id": protein_id})
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame, FeatureLoadSummary(row_count=0, chunk_size=chunk_size, chunk_count=0)
        frame[EMBEDDING_COLUMN] = frame[EMBEDDING_COLUMN].map(_normalize_embedding)
        frame = _coerce_numeric_columns(frame)
        frame = frame.sort_values("protein_id").reset_index(drop=True)
        return frame, FeatureLoadSummary(row_count=len(frame), chunk_size=chunk_size, chunk_count=1)

    chunk_count = 0
    offset = 0
    frames: list[pd.DataFrame] = []
    while True:
        rows = client.run(PROTEIN_FEATURE_ROWS_QUERY, {"skip": offset, "limit": chunk_size})
        if not rows:
            break
        chunk = pd.DataFrame(rows)
        chunk[EMBEDDING_COLUMN] = chunk[EMBEDDING_COLUMN].map(_normalize_embedding)
        chunk = _coerce_numeric_columns(chunk)
        frames.append(chunk)
        chunk_count += 1
        offset += len(chunk)
        logger.info("Loaded feature chunk=%s rows=%s", chunk_count, len(chunk))

    if not frames:
        return pd.DataFrame(), FeatureLoadSummary(row_count=0, chunk_size=chunk_size, chunk_count=0)

    frame = pd.concat(frames, axis=0, ignore_index=True)
    frame = frame.sort_values("protein_id").reset_index(drop=True)
    return frame, FeatureLoadSummary(row_count=len(frame), chunk_size=chunk_size, chunk_count=chunk_count)
