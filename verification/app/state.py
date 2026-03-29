from __future__ import annotations

from typing import TypedDict

from verification.schemas.claim_models import ExtractedClaim
from verification.schemas.evidence_models import VerificationInputPayload
from verification.schemas.verification_models import (
    CitationVerificationResult,
    ClaimVerdict,
    ConfidenceSummary,
    GraphVerificationResult,
    HumanReviewStatus,
    ScoreVerificationResult,
    VerifiedPayload,
)


class VerificationState(TypedDict, total=False):
    input_payload: VerificationInputPayload
    extracted_claims: list[ExtractedClaim]
    graph_checks: list[GraphVerificationResult]
    citation_checks: list[CitationVerificationResult]
    score_checks: list[ScoreVerificationResult]
    claim_verdicts: list[ClaimVerdict]
    overall_verdict: str
    confidence_summary: ConfidenceSummary
    warnings: list[str]
    review_required: bool
    review_reasons: list[str]
    review_status: HumanReviewStatus
    final_verified_payload: VerifiedPayload
