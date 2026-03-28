from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from modeling.app.config import Settings
from modeling.app.constants import DATASET_TARGET_NAME, FEATURE_SCHEMA_VERSION
from modeling.app.neo4j_client import Neo4jClient
from modeling.data.feature_loader import load_protein_features

logger = logging.getLogger(__name__)


@dataclass
class DatasetBuildResult:
    dataset_version: str
    dataset_path: Path
    metadata_path: Path
    split_manifest_path: Path
    latest_pointer_path: Path
    row_count: int
    split_counts: dict[str, int]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_artifact_dirs(settings: Settings) -> dict[str, Path]:
    root = settings.artifacts_root
    datasets = root / "datasets"
    manifests = root / "manifests"
    datasets.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "datasets": datasets,
        "manifests": manifests,
    }


def _compute_heuristic_score(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    score = (
        weights["evidence_count"] * np.log1p(frame["evidence_count"])
        + weights["avg_evidence_confidence"] * frame["avg_evidence_confidence"]
        + weights["pathway_count"] * np.log1p(frame["pathway_count"])
        + weights["interaction_count"] * np.log1p(frame["interaction_count"])
        + weights["publication_count"] * np.log1p(frame["publication_count"])
        + weights["max_evidence_confidence"] * frame["max_evidence_confidence"]
    )
    return score.astype(float)


def _apply_label_strategy(frame: pd.DataFrame, settings: Settings) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = frame.copy()
    heuristic_score = _compute_heuristic_score(frame, settings.heuristic_weights)
    frame["heuristic_score"] = heuristic_score

    metadata: dict[str, Any] = {
        "label_strategy": settings.label_strategy,
        "task_type": settings.task_type,
        "heuristic_formula": "weighted(log1p(counts) + confidence aggregates)",
        "heuristic_weights": settings.heuristic_weights,
        "positive_percentile": settings.heuristic_positive_percentile,
        "is_heuristic": True,
    }

    if settings.label_strategy == "heuristic_binary":
        threshold = float(heuristic_score.quantile(1.0 - settings.heuristic_positive_percentile))
        frame["label"] = (heuristic_score >= threshold).astype(int)
        metadata["binary_threshold"] = threshold
    else:
        frame["label"] = heuristic_score.astype(float)
        metadata["binary_threshold"] = None

    if settings.task_type == "classification" and settings.label_strategy != "heuristic_binary":
        threshold = float(heuristic_score.quantile(1.0 - settings.heuristic_positive_percentile))
        frame["label"] = (heuristic_score >= threshold).astype(int)
        metadata["derived_binary_from_score"] = True
        metadata["binary_threshold"] = threshold

    if settings.task_type == "regression" and settings.label_strategy == "heuristic_binary":
        frame["label"] = heuristic_score.astype(float)
        metadata["regression_target_overrode_binary"] = True

    return frame, metadata


def _split_dataset(frame: pd.DataFrame, settings: Settings) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = frame.copy()
    index = frame.index.to_numpy()

    if settings.task_type == "classification":
        stratify = frame["label"] if frame["label"].nunique() > 1 else None
    else:
        stratify = None

    train_val_idx, test_idx = train_test_split(
        index,
        test_size=settings.test_size,
        random_state=settings.train_test_seed,
        stratify=stratify,
    )

    train_val = frame.loc[train_val_idx]
    val_size_relative = settings.validation_size / (1.0 - settings.test_size)

    if settings.task_type == "classification":
        val_stratify = train_val["label"] if train_val["label"].nunique() > 1 else None
    else:
        val_stratify = None

    train_idx, val_idx = train_test_split(
        train_val_idx,
        test_size=val_size_relative,
        random_state=settings.train_test_seed,
        stratify=val_stratify,
    )

    frame["split"] = "train"
    frame.loc[val_idx, "split"] = "validation"
    frame.loc[test_idx, "split"] = "test"

    manifest = {
        "seed": settings.train_test_seed,
        "test_size": settings.test_size,
        "validation_size": settings.validation_size,
        "counts": {
            "train": int((frame["split"] == "train").sum()),
            "validation": int((frame["split"] == "validation").sum()),
            "test": int((frame["split"] == "test").sum()),
        },
        "protein_ids": {
            split: frame.loc[frame["split"] == split, "protein_id"].tolist()
            for split in ("train", "validation", "test")
        },
    }
    return frame, manifest


def build_dataset(settings: Settings, client: Neo4jClient | None = None) -> DatasetBuildResult:
    paths = _ensure_artifact_dirs(settings)
    created_at = _now_utc()
    dataset_version = created_at.strftime("%Y%m%d%H%M%S")

    owns_client = client is None
    if owns_client:
        client = Neo4jClient.from_settings(settings)

    assert client is not None

    try:
        frame, load_summary = load_protein_features(client=client, chunk_size=settings.dataset_chunk_size)
    finally:
        if owns_client:
            client.close()

    if frame.empty:
        raise RuntimeError("No Protein feature rows found in Neo4j. Ensure prior phases populated required properties.")

    frame, label_metadata = _apply_label_strategy(frame, settings)
    frame, split_manifest = _split_dataset(frame, settings)

    dataset_path = paths["datasets"] / f"{DATASET_TARGET_NAME}_{dataset_version}.parquet"
    metadata_path = paths["manifests"] / f"dataset_metadata_{dataset_version}.json"
    split_manifest_path = paths["manifests"] / f"split_manifest_{dataset_version}.json"
    latest_pointer_path = paths["manifests"] / "latest_dataset.json"

    frame.to_parquet(dataset_path, index=False)

    metadata = {
        "dataset_version": dataset_version,
        "dataset_target": DATASET_TARGET_NAME,
        "created_at": created_at.isoformat(),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "row_count": int(len(frame)),
        "columns": frame.columns.tolist(),
        "load_summary": asdict(load_summary),
        "labeling": label_metadata,
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    split_manifest_path.write_text(json.dumps(split_manifest, indent=2), encoding="utf-8")

    latest_pointer = {
        "dataset_version": dataset_version,
        "dataset_path": str(dataset_path),
        "metadata_path": str(metadata_path),
        "split_manifest_path": str(split_manifest_path),
        "created_at": created_at.isoformat(),
    }
    latest_pointer_path.write_text(json.dumps(latest_pointer, indent=2), encoding="utf-8")

    logger.info("Built dataset version=%s rows=%s", dataset_version, len(frame))

    return DatasetBuildResult(
        dataset_version=dataset_version,
        dataset_path=dataset_path,
        metadata_path=metadata_path,
        split_manifest_path=split_manifest_path,
        latest_pointer_path=latest_pointer_path,
        row_count=int(len(frame)),
        split_counts=split_manifest["counts"],
    )


def load_latest_dataset(settings: Settings) -> tuple[pd.DataFrame, dict[str, Any]]:
    latest_path = settings.artifacts_root / "manifests" / "latest_dataset.json"
    if not latest_path.exists():
        raise FileNotFoundError("No latest_dataset.json found. Run `dataset build` first.")

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    dataset_path = Path(latest["dataset_path"])
    if not dataset_path.exists():
        raise FileNotFoundError(f"Latest dataset parquet missing: {dataset_path}")

    frame = pd.read_parquet(dataset_path)
    return frame, latest
