from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mlflow.tracking import MlflowClient

from modeling.app.config import Settings


@dataclass
class RegistryResult:
    model_name: str
    model_version: str
    status: str


def register_model_from_run(
    settings: Settings,
    run_id: str,
    model_artifact_path: str = "model",
    tags: dict[str, str] | None = None,
) -> RegistryResult | None:
    if not settings.mlflow_register_model:
        return None

    import mlflow

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)

    model_uri = f"runs:/{run_id}/{model_artifact_path}"
    registration = mlflow.register_model(model_uri=model_uri, name=settings.model_registry_name)

    client = MlflowClient(tracking_uri=settings.mlflow_tracking_uri)
    if tags:
        for key, value in tags.items():
            client.set_model_version_tag(settings.model_registry_name, registration.version, key, value)

    if settings.model_registry_alias:
        try:
            client.set_registered_model_alias(
                name=settings.model_registry_name,
                alias=settings.model_registry_alias,
                version=registration.version,
            )
        except Exception:
            # Alias support depends on MLflow server/version.
            pass

    return RegistryResult(
        model_name=settings.model_registry_name,
        model_version=str(registration.version),
        status=str(registration.status),
    )
