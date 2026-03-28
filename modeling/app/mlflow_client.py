from __future__ import annotations

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import mlflow
import mlflow.sklearn
from mlflow.entities import Run
from mlflow.tracking import MlflowClient

from .config import Settings


@dataclass
class MLflowClientWrapper:
    settings: Settings

    def __post_init__(self) -> None:
        mlflow.set_tracking_uri(self.settings.mlflow_tracking_uri)
        mlflow.set_experiment(self.settings.mlflow_experiment_name)
        self.client = MlflowClient(tracking_uri=self.settings.mlflow_tracking_uri)

    @contextlib.contextmanager
    def start_run(self, run_name: str | None = None) -> Iterator[Run]:
        with mlflow.start_run(run_name=run_name) as run:
            yield run

    @staticmethod
    def log_params(params: dict[str, Any]) -> None:
        mlflow.log_params(params)

    @staticmethod
    def log_metrics(metrics: dict[str, float]) -> None:
        mlflow.log_metrics(metrics)

    @staticmethod
    def log_artifact(path: str | Path, artifact_path: str | None = None) -> None:
        mlflow.log_artifact(str(path), artifact_path=artifact_path)

    @staticmethod
    def log_artifacts(path: str | Path, artifact_path: str | None = None) -> None:
        mlflow.log_artifacts(str(path), artifact_path=artifact_path)

    @staticmethod
    def log_model(model: Any, artifact_path: str) -> None:
        mlflow.sklearn.log_model(sk_model=model, artifact_path=artifact_path)

    def register_model(self, model_uri: str, model_name: str) -> Any:
        return mlflow.register_model(model_uri=model_uri, name=model_name)
