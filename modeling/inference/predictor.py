from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
import pandas as pd

from modeling.app.config import Settings
from modeling.features.feature_engineering import build_prediction_frame
from modeling.training.persistence import load_pickle, read_json


@dataclass
class LoadedPredictor:
    model: Any
    feature_columns: list[str]
    task_type: str
    model_name: str
    model_version: str
    run_id: str
    source: str

    def predict(self, feature_rows: pd.DataFrame) -> pd.DataFrame:
        matrix = build_prediction_frame(feature_rows, expected_columns=self.feature_columns)
        y_pred = self.model.predict(matrix)

        if self.task_type == "classification" and hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(matrix)
            if probabilities.ndim == 2 and probabilities.shape[1] > 1:
                target_score = probabilities[:, 1]
            else:
                target_score = y_pred
        elif self.task_type == "classification" and hasattr(self.model, "decision_function"):
            target_score = self.model.decision_function(matrix)
        else:
            target_score = y_pred

        output = pd.DataFrame(
            {
                "protein_id": feature_rows["protein_id"].values,
                "predicted_label": y_pred,
                "target_score": target_score,
            }
        )
        return output


def load_predictor(settings: Settings) -> LoadedPredictor:
    latest_training_path = settings.artifacts_root / "manifests" / "latest_training.json"
    if not latest_training_path.exists():
        raise FileNotFoundError("No latest training run found. Train a model first.")

    latest = read_json(latest_training_path)
    feature_manifest = read_json(Path(latest["feature_manifest_path"]))

    model_name = settings.model_registry_name
    model_version = "local"
    source = "local_artifact"

    model = None
    if settings.mlflow_register_model:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        alias = settings.model_registry_alias or "latest"
        model_uri = f"models:/{settings.model_registry_name}@{alias}"
        try:
            model = mlflow.sklearn.load_model(model_uri)
            source = model_uri
            registry_info = latest.get("registry", {}).get("result")
            if registry_info:
                model_version = str(registry_info.get("model_version", "registry"))
        except Exception:
            model = None

    if model is None:
        model = load_pickle(Path(latest["model_path"]))
        source = "local_artifact"

    return LoadedPredictor(
        model=model,
        feature_columns=list(feature_manifest["feature_columns"]),
        task_type=str(latest.get("task_type", settings.task_type)),
        model_name=model_name,
        model_version=model_version,
        run_id=str(latest["run_id"]),
        source=source,
    )
