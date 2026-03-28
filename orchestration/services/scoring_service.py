from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from orchestration.app.constants import SCORE_PROPERTY_DEFAULTS
from orchestration.schemas.evidence_models import ModelScore
from orchestration.services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


@dataclass
class ScoringService:
    neo4j_service: Neo4jService
    score_source: str = "neo4j_property"
    score_name: str = "target_score"
    artifacts_root: Path | None = None
    allow_mock_fallback_data: bool = True
    _artifact_cache: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

    def get_model_score(self, candidate_id: str) -> ModelScore | None:
        source = self.score_source.lower()

        if source == "modeling_artifact":
            artifact_score = self._from_modeling_artifacts(candidate_id)
            if artifact_score is not None:
                return artifact_score

        row = self.neo4j_service.get_model_score_from_neo4j(candidate_id, SCORE_PROPERTY_DEFAULTS)
        if row is None:
            if self.allow_mock_fallback_data:
                row = {
                    "candidate_id": candidate_id,
                    "score_value": 0.0,
                    "model_name": "unavailable",
                    "model_version": "n/a",
                    "run_id": "n/a",
                    "timestamp": None,
                }
            else:
                return None

        return ModelScore(
            candidate_id=str(row.get("candidate_id") or candidate_id),
            score_name=self.score_name,
            score_value=float(row.get("score_value") or 0.0),
            model_name=str(row.get("model_name") or "unknown"),
            model_version=str(row.get("model_version") or "unknown"),
            run_id=str(row.get("run_id") or "unknown"),
            timestamp=(str(row.get("timestamp")) if row.get("timestamp") else None),
        )

    def _from_modeling_artifacts(self, candidate_id: str) -> ModelScore | None:
        if self.artifacts_root is None:
            return None

        if not self._artifact_cache:
            self._artifact_cache = self._load_artifact_cache(self.artifacts_root)

        row = self._artifact_cache.get(candidate_id)
        if row is None:
            return None

        return ModelScore(
            candidate_id=candidate_id,
            score_name=self.score_name,
            score_value=float(row.get("target_score") or 0.0),
            model_name=str(row.get("model_name") or "local_artifact"),
            model_version=str(row.get("model_version") or "local"),
            run_id=str(row.get("run_id") or "unknown"),
            timestamp=str(row.get("timestamp")) if row.get("timestamp") else None,
        )

    def _load_artifact_cache(self, root: Path) -> dict[str, dict[str, Any]]:
        output: dict[str, dict[str, Any]] = {}

        latest_training = root / "manifests" / "latest_training.json"
        run_metadata: dict[str, Any] = {}
        if latest_training.exists():
            try:
                run_metadata = json.loads(latest_training.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Failed to parse latest_training.json: %s", exc)

        candidate_files = [
            root / "reports" / "latest_batch_predictions.csv",
            root / "reports" / "run_all_prediction_sample.csv",
        ]
        csv_path = next((path for path in candidate_files if path.exists()), None)
        if csv_path is None:
            return output

        with csv_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                protein_id = str(row.get("protein_id") or "").strip()
                if not protein_id:
                    continue
                output[protein_id] = {
                    "target_score": row.get("target_score") or 0.0,
                    "run_id": run_metadata.get("run_id", "unknown"),
                    "model_name": run_metadata.get("model_type", "local_artifact"),
                    "model_version": run_metadata.get("registry", {}).get("result", {}).get("model_version", "local"),
                    "timestamp": row.get("created_at"),
                }

        return output
