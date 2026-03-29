from __future__ import annotations

from answering.schemas.answer_models import AnswerStyle
from answering.schemas.citation_models import CitationMap
from answering.schemas.render_models import LLMAnswerDraft
from answering.schemas.verified_payload_models import ClaimVerdict, VerifiedPayload


class FallbackRenderer:
    """Template-only renderer for no-LLM mode."""

    def render(
        self,
        payload: VerifiedPayload,
        citations: CitationMap,
        *,
        style: AnswerStyle,
    ) -> LLMAnswerDraft:
        verdicts = self._supported_verdicts(payload)

        summary_points: list[str] = []
        for verdict in verdicts:
            tags = " ".join(citations.tags_for_claim(verdict.claim.claim_id))
            prefix = "Partially supported" if verdict.final_status.value == "partially_supported" else "Supported"
            summary_points.append(f"{prefix}: {verdict.claim.claim_text} {tags}".strip())

        caveats = self._collect_caveats(payload, verdicts)

        if style == AnswerStyle.CONCISE:
            body = " ".join(summary_points[:2]) if summary_points else "No supported claims were available."
        elif style == AnswerStyle.DETAILED:
            body = "\n".join(f"- {line}" for line in summary_points) if summary_points else "No supported claims were available."
        else:
            technical_lines = []
            for verdict in verdicts:
                support_mode = self._support_mode(verdict)
                tags = " ".join(citations.tags_for_claim(verdict.claim.claim_id))
                technical_lines.append(
                    f"{verdict.claim.claim_id}: {verdict.claim.claim_text} ({support_mode}) {tags}".strip()
                )
            body = "\n".join(technical_lines) if technical_lines else "No supported claims were available."

        return LLMAnswerDraft(
            headline="Grounded answer from verified payload",
            answer_text=body,
            summary_points=summary_points,
            caveats=caveats,
        )

    @staticmethod
    def _supported_verdicts(payload: VerifiedPayload) -> list[ClaimVerdict]:
        return [
            verdict
            for verdict in payload.claim_verdicts
            if verdict.final_status.value in {"supported", "partially_supported"}
        ]

    @staticmethod
    def _collect_caveats(payload: VerifiedPayload, verdicts: list[ClaimVerdict]) -> list[str]:
        caveats: list[str] = []

        partial_claims = [verdict.claim.claim_id for verdict in verdicts if verdict.final_status.value == "partially_supported"]
        for claim_id in partial_claims:
            caveats.append(f"Claim {claim_id} is partially supported and should be interpreted cautiously.")

        allowed_claim_ids = {verdict.claim.claim_id for verdict in verdicts}
        for claim_id, gaps in payload.missing_evidence_index.items():
            if gaps and claim_id in allowed_claim_ids:
                caveats.append(f"Claim {claim_id} has unresolved evidence gaps: {', '.join(gaps)}.")

        for warning in payload.warnings:
            caveats.append(f"Warning: {warning}")

        if payload.review_status.status != "approved":
            caveats.append(f"Review status is {payload.review_status.status}; content may require additional approval.")

        return caveats

    @staticmethod
    def _support_mode(verdict: ClaimVerdict) -> str:
        if verdict.graph_check.direct_support:
            return "direct_support"
        if verdict.graph_check.indirect_support:
            return "indirect_support"
        return "support_unspecified"
