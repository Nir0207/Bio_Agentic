from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel

from orchestration.schemas.evidence_models import ModelScore, ToolExecutionMetadata
from orchestration.services.scoring_service import ScoringService


class ModelScoreRequest(BaseModel):
    candidate_id: str


class ModelScoreResult(BaseModel):
    model_score: ModelScore | None
    execution_metadata: ToolExecutionMetadata


class ScoringTools:
    def __init__(self, service: ScoringService) -> None:
        self.service = service

    def get_model_score(self, request: ModelScoreRequest) -> ModelScoreResult:
        started = datetime.now(timezone.utc).isoformat()
        model_score = self.service.get_model_score(request.candidate_id)
        metadata = ToolExecutionMetadata(
            tool_name="get_model_score",
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            status="ok" if model_score else "empty",
            rows_read=1 if model_score else 0,
            details={"candidate_id": request.candidate_id},
        )
        return ModelScoreResult(model_score=model_score, execution_metadata=metadata)
