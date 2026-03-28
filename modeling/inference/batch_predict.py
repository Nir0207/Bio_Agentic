from __future__ import annotations

import pandas as pd

from modeling.app.config import Settings
from modeling.app.neo4j_client import Neo4jClient
from modeling.data.feature_loader import load_protein_features
from modeling.inference.predictor import load_predictor


def predict_for_protein_id(settings: Settings, protein_id: str) -> pd.DataFrame:
    with Neo4jClient.from_settings(settings) as client:
        rows, _ = load_protein_features(client=client, protein_id=protein_id)

    if rows.empty:
        raise ValueError(f"Protein not found or feature row missing for id={protein_id}")

    predictor = load_predictor(settings)
    return predictor.predict(rows)


def predict_batch(settings: Settings, limit: int | None = None) -> pd.DataFrame:
    with Neo4jClient.from_settings(settings) as client:
        rows, _ = load_protein_features(client=client, chunk_size=settings.dataset_chunk_size)

    if rows.empty:
        raise RuntimeError("No Protein rows available for batch prediction")

    if limit is not None:
        rows = rows.head(limit).copy()

    predictor = load_predictor(settings)
    return predictor.predict(rows)
