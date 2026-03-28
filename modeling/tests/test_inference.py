from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

from modeling.app.config import Settings
from modeling.inference.predictor import load_predictor
from modeling.training.persistence import build_writeback_payload, save_pickle, write_json


def _setup_model_artifacts(artifacts_root: Path) -> Settings:
    manifests = artifacts_root / "manifests"
    model_dir = artifacts_root / "models" / "test" / "run"
    manifests.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    x = pd.DataFrame({"f1": [0.0, 1.0, 0.0, 1.0], "f2": [0.2, 0.8, 0.1, 0.9]})
    y = pd.Series([0, 1, 0, 1])
    model = LogisticRegression().fit(x, y)

    model_path = save_pickle(model, model_dir / "model.pkl")
    feature_manifest_path = write_json(
        {
            "feature_columns": ["f1", "f2"],
            "feature_schema_version": "v1",
            "feature_count": 2,
            "embedding_dim": 0,
        },
        model_dir / "feature_manifest.json",
    )

    write_json(
        {
            "run_id": "run-123",
            "dataset_version": "test",
            "task_type": "classification",
            "model_path": str(model_path),
            "feature_manifest_path": str(feature_manifest_path),
            "metrics_path": str(model_dir / "metrics.json"),
            "registry": {"enabled": False, "result": None},
        },
        manifests / "latest_training.json",
    )

    return Settings(_env_file=None, artifacts_dir=str(artifacts_root), mlflow_register_model=False)


def test_predictor_load_and_predict(tmp_path: Path) -> None:
    settings = _setup_model_artifacts(tmp_path / "artifacts")
    predictor = load_predictor(settings)

    rows = pd.DataFrame(
        {
            "protein_id": ["P1", "P2"],
            "f1": [0.0, 1.0],
            "f2": [0.1, 0.9],
            "graph_embedding": [[], []],
            "community_id": ["x", "y"],
        }
    )
    prediction = predictor.predict(rows)

    assert list(prediction.columns) == ["protein_id", "predicted_label", "target_score"]
    assert len(prediction) == 2


def test_writeback_payload_generation() -> None:
    predictions = pd.DataFrame(
        {
            "protein_id": ["P1", "P2"],
            "target_score": [0.8, 0.2],
        }
    )

    payload = build_writeback_payload(
        predictions=predictions,
        model_name="protein_target_model",
        model_version="5",
        run_id="run-123",
    )

    assert len(payload) == 2
    assert payload[0]["protein_id"] == "P1"
    assert payload[0]["target_score_model_version"] == "5"
