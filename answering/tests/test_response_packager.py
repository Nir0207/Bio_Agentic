from __future__ import annotations

import json
from pathlib import Path

from answering.app.config import Settings
from answering.renderers.evidence_renderer import EvidenceAppendixRenderer
from answering.schemas.answer_models import AnswerStyle, ModelInfo
from answering.schemas.render_models import LLMAnswerDraft
from answering.schemas.verified_payload_models import VerifiedPayload
from answering.services.answer_renderer import AnswerRenderer
from answering.services.citation_formatter import CitationFormatter
from answering.services.response_packager import ResponsePackager


def _sample_payload() -> VerifiedPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_verified_payload.json"
    return VerifiedPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_response_packager_generates_normalized_schema() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)
    rendered = AnswerRenderer().render(
        payload,
        LLMAnswerDraft(headline="Grounded answer", answer_text="", summary_points=[], caveats=[]),
        citations,
        style=AnswerStyle.TECHNICAL,
    )
    appendix = EvidenceAppendixRenderer().render(
        payload,
        citations,
        settings=Settings(_env_file=None, enable_optional_enrichment=False),
    )

    final_payload = ResponsePackager().package(
        payload,
        rendered,
        citations,
        answer_style=AnswerStyle.TECHNICAL,
        model_info=ModelInfo(provider="fallback", model_name="template", temperature=0, fallback_used=True),
        evidence_appendix=appendix,
    )

    dumped = final_payload.model_dump(mode="json")
    expected_keys = {
        "answer_id",
        "original_query",
        "answer_text",
        "answer_style",
        "summary_points",
        "supported_claims_rendered",
        "caveats",
        "citations",
        "evidence_appendix",
        "overall_confidence",
        "overall_verdict",
        "generated_at",
        "model_info",
        "source_payload_version",
        "review_status",
    }

    assert expected_keys.issubset(dumped.keys())
    assert dumped["review_status"] == "approved_with_caveats"


def test_response_packager_preserves_source_payload_version() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)
    rendered = AnswerRenderer().render(
        payload,
        LLMAnswerDraft(headline="Grounded answer", answer_text="", summary_points=[], caveats=[]),
        citations,
        style=AnswerStyle.CONCISE,
    )
    appendix = EvidenceAppendixRenderer().render(
        payload,
        citations,
        settings=Settings(_env_file=None, enable_optional_enrichment=False),
    )

    final_payload = ResponsePackager().package(
        payload,
        rendered,
        citations,
        answer_style=AnswerStyle.CONCISE,
        model_info=ModelInfo(provider="fallback", model_name="template", temperature=0, fallback_used=True),
        evidence_appendix=appendix,
    )

    assert final_payload.source_payload_version == "1.0.0"
