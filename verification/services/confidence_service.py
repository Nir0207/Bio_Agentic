from __future__ import annotations

from verification.schemas.verification_models import ClaimFinalStatus, ClaimVerdict, ConfidenceSummary


class ConfidenceService:
    """Computes confidence with deterministic penalties for gaps."""

    def summarize(self, claim_verdicts: list[ClaimVerdict]) -> ConfidenceSummary:
        unsupported = 0
        partial = 0
        missing_citations = 0
        warnings: list[str] = []

        score = 0.92

        for verdict in claim_verdicts:
            if verdict.final_status == ClaimFinalStatus.UNSUPPORTED:
                unsupported += 1
                score -= 0.22
            elif verdict.final_status == ClaimFinalStatus.PARTIALLY_SUPPORTED:
                partial += 1
                score -= 0.10
            elif verdict.final_status == ClaimFinalStatus.NEEDS_REVIEW:
                partial += 1
                score -= 0.15

            if verdict.citation_check.citation_supported == "false":
                missing_citations += 1
                score -= 0.08
            elif verdict.citation_check.citation_supported == "partial":
                score -= 0.04

            if verdict.graph_check.graph_supported == "partial" and verdict.graph_check.indirect_support:
                score -= 0.03

            if verdict.score_check.score_supported == "false":
                score -= 0.05

        score = max(0.0, min(1.0, round(score, 3)))

        if unsupported:
            warnings.append(f"{unsupported} claim(s) are unsupported.")
        if partial:
            warnings.append(f"{partial} claim(s) are partially supported or require review.")
        if missing_citations:
            warnings.append(f"{missing_citations} claim(s) are missing citation coverage.")

        return ConfidenceSummary(
            overall_confidence=score,
            unsupported_claim_count=unsupported,
            partially_supported_claim_count=partial,
            missing_citation_count=missing_citations,
            warnings=warnings,
        )
