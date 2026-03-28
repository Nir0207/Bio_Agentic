from __future__ import annotations

from pathlib import Path

import pandas as pd

from modeling.app.config import Settings
from modeling.training.train import evaluate_latest_run, train_baseline_model


def _write_dataset_artifacts(artifacts_root: Path) -> None:
    datasets_dir = artifacts_root / "datasets"
    manifests_dir = artifacts_root / "manifests"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    frame = pd.DataFrame(
        {
            "protein_id": [f"P{i:05d}" for i in range(60)],
            "interaction_count": [float((i % 10) + 1) for i in range(60)],
            "pathway_count": [float((i % 7) + 1) for i in range(60)],
            "evidence_count": [float((i % 6) + 1) for i in range(60)],
            "publication_count": [float((i % 5) + 1) for i in range(60)],
            "avg_evidence_confidence": [0.4 + 0.01 * (i % 10) for i in range(60)],
            "max_evidence_confidence": [0.6 + 0.01 * (i % 10) for i in range(60)],
            "degree_centrality_like_count": [float((i % 10) + 1) for i in range(60)],
            "similar_to_neighbor_count": [float(i % 3) for i in range(60)],
            "avg_similarity_score": [0.1 * (i % 5) for i in range(60)],
            "semantic_similarity_avg": [0.05 * (i % 5) for i in range(60)],
            "community_id": [str(i % 4) for i in range(60)],
            "graph_embedding": [[0.1 * (i % 3), 0.2, 0.3] for i in range(60)],
            "label": [1 if i % 2 == 0 else 0 for i in range(60)],
            "split": ["train" if i < 40 else "validation" if i < 50 else "test" for i in range(60)],
        }
    )

    dataset_path = datasets_dir / "protein_target_prioritization_test.parquet"
    frame.to_parquet(dataset_path, index=False)

    metadata_path = manifests_dir / "dataset_metadata_test.json"
    metadata_path.write_text("{}", encoding="utf-8")

    split_manifest_path = manifests_dir / "split_manifest_test.json"
    split_manifest_path.write_text("{}", encoding="utf-8")

    latest_dataset = manifests_dir / "latest_dataset.json"
    latest_dataset.write_text(
        (
            "{"
            f'"dataset_version":"test",'
            f'"dataset_path":"{dataset_path}",'
            f'"metadata_path":"{metadata_path}",'
            f'"split_manifest_path":"{split_manifest_path}"'
            "}"
        ),
        encoding="utf-8",
    )


def test_train_and_evaluate_flow(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    _write_dataset_artifacts(artifacts_root)

    settings = Settings(
        _env_file=None,
        artifacts_dir=str(artifacts_root),
        mlflow_tracking_uri=f"file://{tmp_path / 'mlruns'}",
        mlflow_experiment_name="test_modeling",
        mlflow_register_model=False,
        model_type="logistic_regression",
        task_type="classification",
        label_strategy="heuristic_binary",
    )

    result = train_baseline_model(settings=settings, register_model=False)
    eval_summary = evaluate_latest_run(settings)

    assert result.run_id
    assert result.metrics_path.exists()
    assert "validation" in eval_summary["metrics"]
    assert "test" in eval_summary["metrics"]
