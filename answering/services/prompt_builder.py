from __future__ import annotations

import json

from answering.prompts import base_system_prompt, citation_rules_prompt, style_prompt_for
from answering.schemas.answer_models import AnswerStyle
from answering.schemas.citation_models import CitationMap
from answering.schemas.render_models import PromptBundle
from answering.schemas.verified_payload_models import ClaimVerdict, VerifiedPayload


class PromptBuilder:
    """Constructs prompts strictly from verified payload content."""

    def build(
        self,
        payload: VerifiedPayload,
        citations: CitationMap,
        *,
        style: AnswerStyle,
    ) -> PromptBundle:
        supported_claims = [
            self._claim_prompt_block(verdict, citations)
            for verdict in self._supported_verdicts(payload)
        ]

        missing_evidence = {
            claim_id: payload.missing_evidence_index.get(claim_id, [])
            for claim_id in [verdict.claim.claim_id for verdict in self._supported_verdicts(payload)]
            if payload.missing_evidence_index.get(claim_id)
        }

        user_payload = {
            "original_query": payload.original_query,
            "overall_verdict": payload.overall_verdict.value,
            "overall_confidence": payload.overall_confidence,
            "review_status": payload.review_status.status,
            "warnings": payload.warnings,
            "supported_claims": supported_claims,
            "missing_evidence": missing_evidence,
            "instructions": [
                "Summarize only the listed claims.",
                "Do not include unsupported claims.",
                "Preserve citation tags in-line.",
                "Call out caveats for partially supported claims.",
            ],
        }

        return PromptBundle(
            system_prompt="\n".join(
                [
                    base_system_prompt(),
                    citation_rules_prompt(),
                    style_prompt_for(style),
                ]
            ),
            user_prompt=json.dumps(user_payload, indent=2),
            answer_style=style,
        )

    @staticmethod
    def _supported_verdicts(payload: VerifiedPayload) -> list[ClaimVerdict]:
        return [
            verdict
            for verdict in payload.claim_verdicts
            if verdict.final_status.value in {"supported", "partially_supported"}
        ]

    @staticmethod
    def _claim_prompt_block(verdict: ClaimVerdict, citations: CitationMap) -> dict:
        tags = citations.tags_for_claim(verdict.claim.claim_id)
        return {
            "claim_id": verdict.claim.claim_id,
            "claim_text": verdict.claim.claim_text,
            "support_status": verdict.final_status.value,
            "direct_support": verdict.graph_check.direct_support,
            "indirect_support": verdict.graph_check.indirect_support,
            "claim_reasons": verdict.reasons,
            "citation_tags": tags,
            "graph_evidence_ids": verdict.graph_check.supporting_graph_evidence_ids,
            "publication_or_evidence_ids": verdict.citation_check.supporting_citation_ids,
            "score_support_ids": [
                f"{block.get('candidate_id')}:{block.get('score_name')}"
                for block in verdict.score_check.supporting_score_blocks
                if block.get("candidate_id") and block.get("score_name")
            ],
        }
