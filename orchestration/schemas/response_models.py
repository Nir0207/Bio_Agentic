from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import ConfidenceSummary, EvidenceBundle, GraphPath, ModelScore, ProvenanceRecord, SemanticHit


class FinalPayload(BaseModel):
    user_query: str
    normalized_query: str
    intent_type: str
    target_entity_ids: list[str] = Field(default_factory=list)
    candidate_entities: list[CandidateEntity] = Field(default_factory=list)
    graph_evidence: list[GraphPath] = Field(default_factory=list)
    semantic_evidence: list[SemanticHit] = Field(default_factory=list)
    model_scores: list[ModelScore] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    confidence_summary: dict[str, ConfidenceSummary] = Field(default_factory=dict)
    evidence_bundle: list[EvidenceBundle] = Field(default_factory=list)
    needs_human_review: bool = False
    review_reason: str | None = None
    status: str = "ready"
    errors: list[str] = Field(default_factory=list)
    execution_metadata: dict[str, Any] = Field(default_factory=dict)
