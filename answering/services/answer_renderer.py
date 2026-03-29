from __future__ import annotations

from answering.schemas.answer_models import AnswerStyle, RenderedClaim
from answering.schemas.citation_models import CitationMap
from answering.schemas.render_models import LLMAnswerDraft, RenderedAnswer
from answering.schemas.verified_payload_models import ClaimVerdict, VerifiedPayload


class AnswerRenderer:
    """Renders final user-facing answer text from verified claims and optional LLM draft."""

    def render(
        self,
        payload: VerifiedPayload,
        draft: LLMAnswerDraft,
        citations: CitationMap,
        *,
        style: AnswerStyle,
    ) -> RenderedAnswer:
        verdicts = self._supported_verdicts(payload)
        rendered_claims = [self._render_claim(verdict, citations) for verdict in verdicts]

        summary_points = draft.summary_points if draft.summary_points else [claim.claim_text for claim in rendered_claims]
        caveats = self._merge_caveats(payload, draft.caveats, verdicts)
        body = self._build_body(style=style, rendered_claims=rendered_claims, caveats=caveats)

        return RenderedAnswer(
            headline=draft.headline or "Grounded answer",
            answer_text=body,
            summary_points=summary_points,
            caveats=caveats,
            supported_claims=rendered_claims,
        )

    @staticmethod
    def _supported_verdicts(payload: VerifiedPayload) -> list[ClaimVerdict]:
        return [
            verdict
            for verdict in payload.claim_verdicts
            if verdict.final_status.value in {"supported", "partially_supported"}
        ]

    def _render_claim(self, verdict: ClaimVerdict, citations: CitationMap) -> RenderedClaim:
        claim_text = verdict.claim.claim_text.strip()
        qualification = None
        if verdict.final_status.value == "partially_supported":
            qualification = "Partially supported; interpret as directional rather than definitive."
            claim_text = f"Partially supported: {claim_text}"

        support_mode = self._support_mode(verdict)
        if support_mode and qualification is None:
            qualification = support_mode

        return RenderedClaim(
            claim_id=verdict.claim.claim_id,
            support_status=verdict.final_status.value,
            claim_text=claim_text,
            qualification=qualification,
            citation_tags=citations.tags_for_claim(verdict.claim.claim_id),
        )

    def _build_body(
        self,
        *,
        style: AnswerStyle,
        rendered_claims: list[RenderedClaim],
        caveats: list[str],
    ) -> str:
        claim_lines = [self._claim_line(claim, style=style) for claim in rendered_claims]

        if style == AnswerStyle.CONCISE:
            limited = claim_lines[:2]
            caveat_line = f"Caveat: {caveats[0]}" if caveats else ""
            pieces = limited + ([caveat_line] if caveat_line else [])
            return "\n".join(pieces).strip()

        if style == AnswerStyle.DETAILED:
            lines = ["Evidence-backed findings:"]
            lines.extend([f"- {line}" for line in claim_lines])
            if caveats:
                lines.append("Caveats:")
                lines.extend([f"- {item}" for item in caveats])
            return "\n".join(lines)

        lines = ["Technical findings:"]
        lines.extend([f"- {line}" for line in claim_lines])
        if caveats:
            lines.append("Caveats:")
            lines.extend([f"- {item}" for item in caveats])
        return "\n".join(lines)

    @staticmethod
    def _claim_line(claim: RenderedClaim, *, style: AnswerStyle) -> str:
        tags = " ".join(claim.citation_tags)
        if style == AnswerStyle.TECHNICAL and claim.qualification:
            return f"{claim.claim_text} ({claim.qualification}) {tags}".strip()
        return f"{claim.claim_text} {tags}".strip()

    def _merge_caveats(
        self,
        payload: VerifiedPayload,
        llm_caveats: list[str],
        verdicts: list[ClaimVerdict],
    ) -> list[str]:
        caveats: list[str] = [item for item in llm_caveats if item.strip()]
        lower_caveats = [item.lower() for item in caveats]

        for verdict in verdicts:
            if verdict.final_status.value == "partially_supported":
                claim_id = verdict.claim.claim_id.lower()
                if not any(claim_id in item and "partially supported" in item for item in lower_caveats):
                    message = f"Claim {verdict.claim.claim_id} is partially supported."
                    caveats.append(message)
                    lower_caveats.append(message.lower())

        allowed_claim_ids = {verdict.claim.claim_id for verdict in verdicts}
        for claim_id, gaps in payload.missing_evidence_index.items():
            if gaps and claim_id in allowed_claim_ids:
                normalized_claim_id = claim_id.lower()
                has_existing_gap = any(
                    normalized_claim_id in item and ("missing evidence" in item or "unresolved evidence gaps" in item)
                    for item in lower_caveats
                )
                if not has_existing_gap:
                    message = f"Claim {claim_id} has missing evidence: {', '.join(gaps)}."
                    caveats.append(message)
                    lower_caveats.append(message.lower())

        if payload.review_status.status != "approved":
            if not any("review status" in item for item in lower_caveats):
                message = f"Review status is '{payload.review_status.status}', so downstream approval may still be required."
                caveats.append(message)
                lower_caveats.append(message.lower())

        for warning in payload.warnings:
            warning_line = f"Warning: {warning}"
            if warning_line.lower() not in lower_caveats:
                caveats.append(warning_line)
                lower_caveats.append(warning_line.lower())

        # Preserve order while removing duplicates.
        deduped: list[str] = []
        seen: set[str] = set()
        for item in caveats:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    @staticmethod
    def _support_mode(verdict: ClaimVerdict) -> str | None:
        if verdict.graph_check.direct_support:
            return "Direct graph support"
        if verdict.graph_check.indirect_support:
            return "Indirect graph support"
        return None
