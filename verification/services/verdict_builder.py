from __future__ import annotations

from verification.app.config import Settings
from verification.schemas.claim_models import ExtractedClaim
from verification.schemas.evidence_models import VerificationInputPayload
from verification.schemas.verification_models import (
    CitationVerificationResult,
    ClaimFinalStatus,
    ClaimVerdict,
    GraphVerificationResult,
    OverallVerdict,
    ScoreVerificationResult,
    VerificationComputation,
)
from verification.services.confidence_service import ConfidenceService


class VerdictBuilder:
    """Build claim-level and overall verdicts from check outputs."""

    def __init__(self, confidence_service: ConfidenceService | None = None) -> None:
        self._confidence_service = confidence_service or ConfidenceService()

    def build(
        self,
        *,
        payload: VerificationInputPayload,
        claims: list[ExtractedClaim],
        graph_checks: list[GraphVerificationResult],
        citation_checks: list[CitationVerificationResult],
        score_checks: list[ScoreVerificationResult],
        settings: Settings,
    ) -> VerificationComputation:
        graph_by_claim = {item.claim_id: item for item in graph_checks}
        citation_by_claim = {item.claim_id: item for item in citation_checks}
        score_by_claim = {item.claim_id: item for item in score_checks}

        claim_verdicts: list[ClaimVerdict] = []
        contradictory_claims: list[str] = []
        unsupported_critical_claims: list[str] = []

        for claim in claims:
            graph_check = graph_by_claim[claim.claim_id]
            citation_check = citation_by_claim[claim.claim_id]
            score_check = score_by_claim[claim.claim_id]

            final_status, reasons = self._claim_status(claim, graph_check, citation_check, score_check)

            if graph_check.graph_supported == "false" and citation_check.citation_supported == "true":
                contradictory_claims.append(claim.claim_id)
                reasons.append("Graph evidence contradicts citation support and requires analyst review.")
                final_status = ClaimFinalStatus.NEEDS_REVIEW

            if claim.critical and final_status in {ClaimFinalStatus.UNSUPPORTED, ClaimFinalStatus.PARTIALLY_SUPPORTED, ClaimFinalStatus.NEEDS_REVIEW}:
                unsupported_critical_claims.append(claim.claim_id)
                final_status = ClaimFinalStatus.NEEDS_REVIEW
                reasons.append("Critical/high-stakes claim is not fully supported.")

            claim_verdicts.append(
                ClaimVerdict(
                    claim=claim,
                    graph_check=graph_check,
                    citation_check=citation_check,
                    score_check=score_check,
                    final_status=final_status,
                    reasons=sorted(set(reasons)),
                )
            )

        confidence_summary = self._confidence_service.summarize(claim_verdicts)

        review_reasons: list[str] = []
        review_required = False

        if unsupported_critical_claims:
            review_required = True
            review_reasons.append("Unsupported critical claims detected.")

        if payload.high_stakes and settings.review_high_stakes:
            review_required = True
            review_reasons.append("High-stakes query requires human review.")

        if contradictory_claims and settings.review_on_contradiction:
            review_required = True
            review_reasons.append("Contradictory evidence across modalities detected.")

        if settings.min_citations_per_claim > 0 and confidence_summary.missing_citation_count >= settings.min_citations_per_claim:
            review_required = True
            review_reasons.append("Citation coverage below required minimum.")

        if confidence_summary.overall_confidence < settings.low_confidence_threshold:
            review_required = True
            review_reasons.append("Overall confidence below threshold.")

        unsupported_count = confidence_summary.unsupported_claim_count
        partial_count = confidence_summary.partially_supported_claim_count

        if review_required:
            verdict = OverallVerdict.REVIEW_REQUIRED
        elif unsupported_count == 0 and partial_count == 0:
            verdict = OverallVerdict.APPROVED
        elif unsupported_count == 0:
            verdict = OverallVerdict.APPROVED_WITH_CAVEATS
        elif unsupported_count >= max(1, len(claims) // 2):
            verdict = OverallVerdict.REJECTED
        else:
            verdict = OverallVerdict.APPROVED_WITH_CAVEATS

        warnings = list(confidence_summary.warnings)
        if contradictory_claims:
            warnings.append(f"Contradictory support detected for claims: {', '.join(contradictory_claims)}.")

        return VerificationComputation(
            claim_verdicts=claim_verdicts,
            overall_verdict=verdict,
            confidence_summary=confidence_summary,
            review_required=review_required,
            review_reasons=sorted(set(review_reasons)),
            warnings=warnings,
        )

    def _claim_status(
        self,
        claim: ExtractedClaim,
        graph_check: GraphVerificationResult,
        citation_check: CitationVerificationResult,
        score_check: ScoreVerificationResult,
    ) -> tuple[ClaimFinalStatus, list[str]]:
        reasons: list[str] = []

        levels = [
            graph_check.graph_supported,
            citation_check.citation_supported,
            score_check.score_supported,
        ]

        if graph_check.graph_supported == "false":
            reasons.append(graph_check.unsupported_reason or "Graph support missing.")
        if citation_check.citation_supported == "false":
            reasons.append(citation_check.missing_citation_reason or "Citation support missing.")
        if score_check.score_supported == "false":
            reasons.append("Score claim not supported by available score metadata.")

        if all(level == "true" for level in levels):
            return ClaimFinalStatus.SUPPORTED, reasons

        if all(level == "false" for level in levels):
            return ClaimFinalStatus.UNSUPPORTED, reasons

        if "false" in levels:
            return ClaimFinalStatus.PARTIALLY_SUPPORTED, reasons

        if "partial" in levels:
            return ClaimFinalStatus.PARTIALLY_SUPPORTED, reasons

        if claim.critical:
            return ClaimFinalStatus.NEEDS_REVIEW, reasons

        return ClaimFinalStatus.SUPPORTED, reasons
