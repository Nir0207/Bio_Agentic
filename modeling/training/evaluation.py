from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

matplotlib.use("Agg")


@dataclass
class EvaluationResult:
    metrics: dict[str, float]
    predictions: pd.DataFrame
    confusion_matrix_path: Path | None
    residual_plot_path: Path | None
    feature_importance_path: Path | None


def _classification_metrics(y_true: pd.Series, y_pred: pd.Series, y_score: pd.Series | None) -> dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if y_score is not None and y_true.nunique() > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
    return metrics


def _regression_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    return {
        "rmse": float(mean_squared_error(y_true, y_pred, squared=False)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _save_confusion_matrix(y_true: pd.Series, y_pred: pd.Series, output_path: Path) -> Path:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(cm, cmap="Blues")
    ax.set_title("Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    for (i, j), value in pd.DataFrame(cm).stack().items():
        ax.text(j, i, str(value), ha="center", va="center", color="black")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def _save_residual_plot(y_true: pd.Series, y_pred: pd.Series, output_path: Path) -> Path:
    residuals = y_true - y_pred
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(y_pred, residuals, s=12, alpha=0.7)
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_title("Residual Diagnostics")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Residual")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def _extract_feature_importance(model: Any, feature_columns: list[str]) -> pd.DataFrame | None:
    values = None
    if hasattr(model, "feature_importances_"):
        values = getattr(model, "feature_importances_")
    elif hasattr(model, "coef_"):
        coef = getattr(model, "coef_")
        values = coef[0] if getattr(coef, "ndim", 1) > 1 else coef

    if values is None:
        return None

    importance = pd.DataFrame({"feature": feature_columns, "importance": values})
    importance["importance"] = importance["importance"].abs()
    return importance.sort_values("importance", ascending=False).reset_index(drop=True)


def evaluate_model(
    task_type: str,
    protein_ids: pd.Series,
    y_true: pd.Series,
    y_pred: pd.Series,
    y_score: pd.Series | None,
    model: Any,
    feature_columns: list[str],
    output_dir: Path,
    split_name: str,
) -> EvaluationResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    if task_type == "classification":
        metrics = _classification_metrics(y_true, y_pred, y_score)
        confusion_path = _save_confusion_matrix(y_true, y_pred, output_dir / f"confusion_matrix_{split_name}.png")
        residual_path = None
    else:
        metrics = _regression_metrics(y_true, y_pred)
        residual_path = _save_residual_plot(y_true, y_pred, output_dir / f"residuals_{split_name}.png")
        confusion_path = None

    prediction_rows = {
        "protein_id": protein_ids,
        "y_true": y_true,
        "y_pred": y_pred,
    }
    if y_score is not None:
        prediction_rows["y_score"] = y_score

    predictions = pd.DataFrame(prediction_rows)

    importance = _extract_feature_importance(model, feature_columns)
    importance_path: Path | None = None
    if importance is not None and not importance.empty:
        importance_path = output_dir / f"feature_importance_{split_name}.csv"
        importance.to_csv(importance_path, index=False)

    return EvaluationResult(
        metrics=metrics,
        predictions=predictions,
        confusion_matrix_path=confusion_path,
        residual_plot_path=residual_path,
        feature_importance_path=importance_path,
    )


def write_metrics_json(metrics: dict[str, Any], output_path: Path) -> Path:
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return output_path
