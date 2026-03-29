from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from answering.schemas.answer_models import AnswerStyle, CitationReference, FinalAnswerPayload, ModelInfo
from answering.schemas.citation_models import CitationMap
from answering.schemas.render_models import RenderedAnswer
from answering.schemas.verified_payload_models import VerifiedPayload


class ResponsePackager:
    def package(
        self,
        payload: VerifiedPayload,
        rendered: RenderedAnswer,
        citations: CitationMap,
        *,
        answer_style: AnswerStyle,
        model_info: ModelInfo,
        evidence_appendix,
    ) -> FinalAnswerPayload:
        citation_refs = [
            CitationReference(
                citation_tag=entry.citation_tag,
                source_id=entry.source_id,
                source_label=entry.source_label,
                kind=entry.kind,
                claim_ids=entry.claim_ids,
            )
            for entry in citations.entries
        ]

        return FinalAnswerPayload(
            answer_id=str(uuid4()),
            original_query=payload.original_query,
            answer_text=rendered.answer_text,
            answer_style=answer_style,
            summary_points=rendered.summary_points,
            supported_claims_rendered=rendered.supported_claims,
            caveats=rendered.caveats,
            citations=citation_refs,
            evidence_appendix=evidence_appendix,
            overall_confidence=payload.overall_confidence,
            overall_verdict=payload.overall_verdict.value,
            generated_at=datetime.now(timezone.utc),
            model_info=model_info,
            source_payload_version=payload.final_verified_payload_version,
            review_status=payload.review_status.status,
        )
