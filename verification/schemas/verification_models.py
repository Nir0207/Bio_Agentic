from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from verification.schemas.claim_models import ExtractedClaim
from verification.schemas.evidence_models import CandidateEntity

SupportLevel = Literal["true", "false", "partial"]


class ClaimFinalStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    NEEDS_REVIEW = "needs_review"


class OverallVerdict(str, Enum):
    APPROVED = "approved"
    APPROVED_WITH_CAVEATS = "approved_with_caveats"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"


class GraphVerificationResult(BaseModel):
    claim_id: str
    graph_supported: SupportLevel
    supporting_graph_evidence_ids: list[str] = Field(default_factory=list)
    path_count: int = 0
    support_notes: list[str] = Field(default_factory=list)
    unsupported_reason: str | None = None
    direct_support: bool = False
    indirect_support: bool = False


class CitationVerificationResult(BaseModel):
    claim_id: str
    citation_supported: SupportLevel
    supporting_citation_ids: list[str] = Field(default_factory=list)
    missing_citation_reason: str | None = None


class ScoreVerificationResult(BaseModel):
    claim_id: str
    score_supported: SupportLevel
    supporting_score_blocks: list[dict] = Field(default_factory=list)
    score_notes: list[str] = Field(default_factory=list)


class ClaimVerdict(BaseModel):
    claim: ExtractedClaim
    graph_check: GraphVerificationResult
    citation_check: CitationVerificationResult
    score_check: ScoreVerificationResult
    final_status: ClaimFinalStatus
    reasons: list[str] = Field(default_factory=list)


class ConfidenceSummary(BaseModel):
    overall_confidence: float
    unsupported_claim_count: int
    partially_supported_claim_count: int
    missing_citation_count: int
    warnings: list[str] = Field(default_factory=list)


class HumanReviewStatus(BaseModel):
    status: str = "not_required"
    triggered: bool = False
    reasons: list[str] = Field(default_factory=list)
    pending_claim_ids: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    action_taken: str | None = None
    edits_applied: dict = Field(default_factory=dict)


class VerificationComputation(BaseModel):
    claim_verdicts: list[ClaimVerdict]
    overall_verdict: OverallVerdict
    confidence_summary: ConfidenceSummary
    review_required: bool
    review_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class VerifiedPayload(BaseModel):
    original_query: str
    candidate_entities: list[CandidateEntity] = Field(default_factory=list)
    extracted_claims: list[ExtractedClaim] = Field(default_factory=list)
    claim_verdicts: list[ClaimVerdict] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_citations: list[str] = Field(default_factory=list)
    overall_verdict: OverallVerdict
    overall_confidence: float
    confidence_summary: ConfidenceSummary
    supporting_evidence_index: dict[str, list[str]] = Field(default_factory=dict)
    missing_evidence_index: dict[str, list[str]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    review_status: HumanReviewStatus = Field(default_factory=HumanReviewStatus)
    final_verified_payload_version: str
