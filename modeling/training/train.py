from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from modeling.app.config import Settings
from modeling.app.mlflow_client import MLflowClientWrapper
from modeling.data.dataset_builder import load_latest_dataset
from modeling.features.feature_engineering import (
    build_feature_matrix,
    build_training_targets,
    summarize_feature_manifest,
)
from modeling.training.evaluation import evaluate_model, write_metrics_json
from modeling.training.models import build_model, extract_model_hyperparameters
from modeling.training.persistence import read_json, save_pickle, write_json
from modeling.training.registry import RegistryResult, register_model_from_run
from modeling.validation.data_checks import run_data_checks
from modeling.validation.model_checks import run_model_checks

logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    run_id: str
    dataset_version: str
    model_type: str
    task_type: str
    label_strategy: str
    run_dir: Path
    model_path: Path
    metrics_path: Path
    predictions_path: Path
    feature_manifest_path: Path
    summary_path: Path
    registry_result: RegistryResult | None


def _predict_for_task(model: Any, matrix: pd.DataFrame, task_type: str) -> tuple[pd.Series, pd.Series | None]:
    y_pred = pd.Series(model.predict(matrix), index=matrix.index)

    if task_type == "classification":
        if hasattr(model, "predict_proba"):
            probability = model.predict_proba(matrix)
            if probability.ndim == 2 and probability.shape[1] > 1:
                return y_pred, pd.Series(probability[:, 1], index=matrix.index)
        if hasattr(model, "decision_function"):
            decision = model.decision_function(matrix)
            return y_pred, pd.Series(decision, index=matrix.index)

    return y_pred, None


def train_baseline_model(settings: Settings, register_model: bool | None = None) -> TrainingResult:
    run_data = load_latest_dataset(settings)
    dataset, dataset_pointer = run_data

    checks = run_data_checks(dataset, task_type=settings.task_type)
    if checks["errors"]:
        raise ValueError(f"Dataset checks failed: {checks['errors']}")

    feature_matrix = build_feature_matrix(dataset)
    targets = build_training_targets(dataset)

    train_mask = dataset["split"] == "train"
    validation_mask = dataset["split"] == "validation"
    test_mask = dataset["split"] == "test"

    x_train = feature_matrix.matrix.loc[train_mask]
    x_validation = feature_matrix.matrix.loc[validation_mask]
    x_test = feature_matrix.matrix.loc[test_mask]

    y_train = targets.loc[train_mask]
    y_validation = targets.loc[validation_mask]
    y_test = targets.loc[test_mask]

    model = build_model(settings)
    model.fit(x_train, y_train)

    run_model_checks(model, x_validation, task_type=settings.task_type)

    y_validation_pred, y_validation_score = _predict_for_task(model, x_validation, settings.task_type)
    validation_eval = evaluate_model(
        task_type=settings.task_type,
        protein_ids=dataset.loc[validation_mask, "protein_id"],
        y_true=y_validation,
        y_pred=y_validation_pred,
        y_score=y_validation_score,
        model=model,
        feature_columns=feature_matrix.feature_columns,
        output_dir=settings.artifacts_root / "reports",
        split_name="validation",
    )

    y_test_pred, y_test_score = _predict_for_task(model, x_test, settings.task_type)
    test_eval = evaluate_model(
        task_type=settings.task_type,
        protein_ids=dataset.loc[test_mask, "protein_id"],
        y_true=y_test,
        y_pred=y_test_pred,
        y_score=y_test_score,
        model=model,
        feature_columns=feature_matrix.feature_columns,
        output_dir=settings.artifacts_root / "reports",
        split_name="test",
    )

    created_at = datetime.now(timezone.utc)
    run_dir = settings.artifacts_root / "models" / dataset_pointer["dataset_version"] / created_at.strftime("%Y%m%d%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    model_path = save_pickle(model, run_dir / "model.pkl")
    feature_manifest = summarize_feature_manifest(feature_matrix, dataset_version=dataset_pointer["dataset_version"])
    feature_manifest_path = write_json(feature_manifest, run_dir / "feature_manifest.json")

    predictions = pd.concat(
        [
            pd.DataFrame(
                {
                    "protein_id": dataset.loc[test_mask, "protein_id"].values,
                    "split": "test",
                    "y_true": y_test.values,
                    "y_pred": y_test_pred.values,
                    "target_score": (y_test_score if y_test_score is not None else y_test_pred).values,
                }
            ),
            pd.DataFrame(
                {
                    "protein_id": dataset.loc[validation_mask, "protein_id"].values,
                    "split": "validation",
                    "y_true": y_validation.values,
                    "y_pred": y_validation_pred.values,
                    "target_score": (y_validation_score if y_validation_score is not None else y_validation_pred).values,
                }
            ),
        ],
        ignore_index=True,
    )
    predictions_path = run_dir / "sample_predictions.csv"
    predictions.to_csv(predictions_path, index=False)

    metrics = {
        "validation": validation_eval.metrics,
        "test": test_eval.metrics,
    }
    metrics_path = write_metrics_json(metrics, run_dir / "metrics.json")

    mlflow_client = MLflowClientWrapper(settings)
    with mlflow_client.start_run(run_name=f"baseline_{settings.model_type}_{dataset_pointer['dataset_version']}") as run:
        run_id = run.info.run_id

        mlflow_client.log_params(
            {
                "model_type": settings.model_type,
                "task_type": settings.task_type,
                "label_strategy": settings.label_strategy,
                "feature_schema_version": feature_manifest["feature_schema_version"],
                "dataset_version": dataset_pointer["dataset_version"],
                "train_rows": int(train_mask.sum()),
                "validation_rows": int(validation_mask.sum()),
                "test_rows": int(test_mask.sum()),
                **extract_model_hyperparameters(model),
            }
        )

        flattened_metrics = {
            **{f"validation_{name}": value for name, value in validation_eval.metrics.items()},
            **{f"test_{name}": value for name, value in test_eval.metrics.items()},
        }
        mlflow_client.log_metrics(flattened_metrics)
        mlflow_client.log_model(model, artifact_path="model")

        mlflow_client.log_artifact(metrics_path, artifact_path="reports")
        mlflow_client.log_artifact(feature_manifest_path, artifact_path="manifests")
        mlflow_client.log_artifact(predictions_path, artifact_path="reports")
        mlflow_client.log_artifact(Path(dataset_pointer["metadata_path"]), artifact_path="manifests")
        mlflow_client.log_artifact(Path(dataset_pointer["split_manifest_path"]), artifact_path="manifests")
        if validation_eval.feature_importance_path:
            mlflow_client.log_artifact(validation_eval.feature_importance_path, artifact_path="reports")
        if validation_eval.confusion_matrix_path:
            mlflow_client.log_artifact(validation_eval.confusion_matrix_path, artifact_path="reports")
        if test_eval.confusion_matrix_path:
            mlflow_client.log_artifact(test_eval.confusion_matrix_path, artifact_path="reports")
        if validation_eval.residual_plot_path:
            mlflow_client.log_artifact(validation_eval.residual_plot_path, artifact_path="reports")
        if test_eval.residual_plot_path:
            mlflow_client.log_artifact(test_eval.residual_plot_path, artifact_path="reports")

    registry_enabled = settings.mlflow_register_model if register_model is None else register_model
    registry_result = None
    if registry_enabled:
        registry_result = register_model_from_run(
            settings=settings,
            run_id=run_id,
            model_artifact_path="model",
            tags={
                "task_type": settings.task_type,
                "dataset_version": dataset_pointer["dataset_version"],
                "label_strategy": settings.label_strategy,
            },
        )

    summary = {
        "run_id": run_id,
        "dataset_version": dataset_pointer["dataset_version"],
        "model_type": settings.model_type,
        "task_type": settings.task_type,
        "label_strategy": settings.label_strategy,
        "model_path": str(model_path),
        "feature_manifest_path": str(feature_manifest_path),
        "metrics_path": str(metrics_path),
        "predictions_path": str(predictions_path),
        "registry": {
            "enabled": registry_enabled,
            "result": (
                {
                    "model_name": registry_result.model_name,
                    "model_version": registry_result.model_version,
                    "status": registry_result.status,
                }
                if registry_result
                else None
            ),
        },
    }

    summary_path = write_json(summary, run_dir / "run_summary.json")
    latest_training_path = settings.artifacts_root / "manifests" / "latest_training.json"
    write_json(summary, latest_training_path)

    return TrainingResult(
        run_id=run_id,
        dataset_version=dataset_pointer["dataset_version"],
        model_type=settings.model_type,
        task_type=settings.task_type,
        label_strategy=settings.label_strategy,
        run_dir=run_dir,
        model_path=model_path,
        metrics_path=metrics_path,
        predictions_path=predictions_path,
        feature_manifest_path=feature_manifest_path,
        summary_path=summary_path,
        registry_result=registry_result,
    )


def evaluate_latest_run(settings: Settings) -> dict[str, Any]:
    latest_training_path = settings.artifacts_root / "manifests" / "latest_training.json"
    if not latest_training_path.exists():
        raise FileNotFoundError("No latest training summary found. Run `train baseline` first.")

    summary = read_json(latest_training_path)
    metrics_path = Path(summary["metrics_path"])
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    metrics = read_json(metrics_path)
    return {
        "run_id": summary["run_id"],
        "dataset_version": summary["dataset_version"],
        "metrics": metrics,
        "summary_path": str(latest_training_path),
    }
