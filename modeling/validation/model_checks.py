from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_WRITEBACK_KEYS = {
    "protein_id",
    "target_score",
    "target_score_model_name",
    "target_score_model_version",
    "target_score_run_id",
    "target_score_created_at",
}


def run_model_checks(model: object, sample_matrix: pd.DataFrame, task_type: str) -> None:
    if not hasattr(model, "predict"):
        raise ValueError("Model does not implement predict()")

    predictions = model.predict(sample_matrix)
    if len(predictions) != len(sample_matrix):
        raise ValueError("Prediction length mismatch")

    if task_type == "classification":
        if not hasattr(model, "predict_proba") and not hasattr(model, "decision_function"):
            raise ValueError("Classification model should expose predict_proba() or decision_function()")

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(sample_matrix)
            if probabilities.ndim != 2:
                raise ValueError("predict_proba() should return a 2D array")


def validate_writeback_payload(payload: list[dict[str, object]]) -> None:
    for item in payload:
        missing = REQUIRED_WRITEBACK_KEYS.difference(item.keys())
        if missing:
            raise ValueError(f"Writeback payload missing keys: {sorted(missing)}")

        score = float(item["target_score"])
        if not np.isfinite(score):
            raise ValueError("Writeback payload contains non-finite score")
