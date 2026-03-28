from __future__ import annotations

from pathlib import Path

from modeling.app.config import Settings
from modeling.app.mlflow_client import MLflowClientWrapper


def test_mlflow_wrapper_invokes_tracking_setup(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_set_tracking_uri(uri: str) -> None:
        captured["tracking_uri"] = uri

    def fake_set_experiment(name: str) -> None:
        captured["experiment"] = name

    monkeypatch.setattr("modeling.app.mlflow_client.mlflow.set_tracking_uri", fake_set_tracking_uri)
    monkeypatch.setattr("modeling.app.mlflow_client.mlflow.set_experiment", fake_set_experiment)

    settings = Settings(
        _env_file=None,
        mlflow_tracking_uri=f"file://{tmp_path / 'mlruns'}",
        mlflow_experiment_name="unit-test-exp",
    )

    MLflowClientWrapper(settings)

    assert captured["tracking_uri"] == settings.mlflow_tracking_uri
    assert captured["experiment"] == "unit-test-exp"
