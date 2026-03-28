from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from modeling.app.constants import TARGET_SCORE_PROPERTIES
from modeling.app.neo4j_client import Neo4jClient


def save_pickle(obj: Any, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as file_handle:
        pickle.dump(obj, file_handle)
    return output_path


def load_pickle(input_path: Path) -> Any:
    with input_path.open("rb") as file_handle:
        return pickle.load(file_handle)


def write_json(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def chunked(sequence: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for idx in range(0, len(sequence), size):
        yield sequence[idx : idx + size]


def build_writeback_payload(
    predictions: pd.DataFrame,
    model_name: str,
    model_version: str,
    run_id: str,
) -> list[dict[str, Any]]:
    created_at = datetime.now(timezone.utc).isoformat()
    payload: list[dict[str, Any]] = []
    for _, row in predictions.iterrows():
        payload.append(
            {
                "protein_id": row["protein_id"],
                "target_score": float(row["target_score"]),
                "target_score_model_name": model_name,
                "target_score_model_version": model_version,
                "target_score_run_id": run_id,
                "target_score_created_at": created_at,
            }
        )
    return payload


def writeback_scores(
    client: Neo4jClient,
    payload: list[dict[str, Any]],
    batch_size: int = 500,
) -> int:
    if not payload:
        return 0

    query = f"""
    UNWIND $rows AS row
    MATCH (p:Protein {{id: row.protein_id}})
    SET p.{TARGET_SCORE_PROPERTIES['score']} = row.target_score,
        p.{TARGET_SCORE_PROPERTIES['model_name']} = row.target_score_model_name,
        p.{TARGET_SCORE_PROPERTIES['model_version']} = row.target_score_model_version,
        p.{TARGET_SCORE_PROPERTIES['run_id']} = row.target_score_run_id,
        p.{TARGET_SCORE_PROPERTIES['created_at']} = row.target_score_created_at
    RETURN count(p) AS updated_count
    """.strip()

    updated = 0
    for batch in chunked(payload, batch_size):
        result = client.run(query, {"rows": batch})
        if result:
            updated += int(result[0].get("updated_count", 0))
    return updated
