from __future__ import annotations

from typing import Any

import pandas as pd


REQUIRED_COLUMNS = {"protein_id", "label", "split"}


def run_data_checks(frame: pd.DataFrame, task_type: str) -> dict[str, list[str] | dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    info: dict[str, Any] = {}

    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        errors.append(f"Missing required columns: {missing}")
        return {"errors": errors, "warnings": warnings, "info": info}

    if frame["protein_id"].isna().any():
        errors.append("protein_id contains nulls")

    duplicated = int(frame["protein_id"].duplicated().sum())
    if duplicated > 0:
        errors.append(f"Duplicate protein_id rows found: {duplicated}")

    split_counts = frame["split"].value_counts().to_dict()
    info["split_counts"] = split_counts
    for split_name in ("train", "validation", "test"):
        if split_counts.get(split_name, 0) == 0:
            errors.append(f"Split '{split_name}' has zero rows")

    if task_type == "classification":
        label_values = sorted(frame["label"].dropna().unique().tolist())
        info["label_values"] = label_values
        if len(label_values) < 2:
            errors.append("Classification dataset needs at least two label classes")

    if "graph_embedding" in frame.columns:
        dims = frame["graph_embedding"].apply(lambda item: len(item) if isinstance(item, list) else 0)
        info["embedding_dim_min"] = int(dims.min())
        info["embedding_dim_max"] = int(dims.max())
        if int(dims.max()) == 0:
            warnings.append("All graph embeddings are empty; model will rely on aggregate features only")

    train_ids = set(frame.loc[frame["split"] == "train", "protein_id"])
    validation_ids = set(frame.loc[frame["split"] == "validation", "protein_id"])
    test_ids = set(frame.loc[frame["split"] == "test", "protein_id"])

    if train_ids.intersection(validation_ids):
        errors.append("Train/validation leakage detected by overlapping protein_id")
    if train_ids.intersection(test_ids):
        errors.append("Train/test leakage detected by overlapping protein_id")
    if validation_ids.intersection(test_ids):
        errors.append("Validation/test leakage detected by overlapping protein_id")

    return {"errors": errors, "warnings": warnings, "info": info}
