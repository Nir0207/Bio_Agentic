from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from answering.schemas.citation_models import CitationKind


class AnswerStyle(str, Enum):
    CONCISE = "concise"
    DETAILED = "detailed"
    TECHNICAL = "technical"


class RenderedClaim(BaseModel):
    claim_id: str
    support_status: str
    claim_text: str
    qualification: str | None = None
    citation_tags: list[str] = Field(default_factory=list)


class CitationReference(BaseModel):
    citation_tag: str
    source_id: str
    source_label: str
    kind: CitationKind
    claim_ids: list[str] = Field(default_factory=list)


class EvidenceAppendix(BaseModel):
    graph_evidence_items: list[str] = Field(default_factory=list)
    publication_and_evidence_citations: list[str] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ModelInfo(BaseModel):
    provider: str
    model_name: str
    temperature: float
    fallback_used: bool = False


class FinalAnswerPayload(BaseModel):
    answer_id: str
    original_query: str
    answer_text: str
    answer_style: AnswerStyle
    summary_points: list[str] = Field(default_factory=list)
    supported_claims_rendered: list[RenderedClaim] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    citations: list[CitationReference] = Field(default_factory=list)
    evidence_appendix: EvidenceAppendix
    overall_confidence: float
    overall_verdict: str
    generated_at: datetime
    model_info: ModelInfo
    source_payload_version: str
    review_status: str = "not_required"
