from __future__ import annotations

import json
from pathlib import Path

from answering.schemas.answer_models import AnswerStyle
from answering.schemas.verified_payload_models import VerifiedPayload
from answering.services.citation_formatter import CitationFormatter
from answering.services.fallback_renderer import FallbackRenderer


def _sample_payload() -> VerifiedPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_verified_payload.json"
    return VerifiedPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_fallback_renderer_supports_all_styles() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)
    renderer = FallbackRenderer()

    concise = renderer.render(payload, citations, style=AnswerStyle.CONCISE)
    detailed = renderer.render(payload, citations, style=AnswerStyle.DETAILED)
    technical = renderer.render(payload, citations, style=AnswerStyle.TECHNICAL)

    assert concise.answer_text
    assert detailed.answer_text
    assert technical.answer_text
    assert "claim-erbb2-higher" not in concise.answer_text


def test_fallback_renderer_surfaces_caveats_and_review_status() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)

    result = FallbackRenderer().render(payload, citations, style=AnswerStyle.TECHNICAL)

    assert any("partially supported" in item.lower() for item in result.caveats)
    assert any("review status" in item.lower() for item in result.caveats)
