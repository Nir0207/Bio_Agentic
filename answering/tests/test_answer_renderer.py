from __future__ import annotations

import json
from pathlib import Path

from answering.app.config import Settings
from answering.renderers.evidence_renderer import EvidenceAppendixRenderer
from answering.renderers.markdown_renderer import MarkdownRenderer
from answering.schemas.answer_models import AnswerStyle
from answering.schemas.render_models import LLMAnswerDraft
from answering.schemas.verified_payload_models import VerifiedPayload
from answering.services.answer_renderer import AnswerRenderer
from answering.services.citation_formatter import CitationFormatter


def _sample_payload() -> VerifiedPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_verified_payload.json"
    return VerifiedPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_answer_renderer_qualifies_partially_supported_claims() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)
    draft = LLMAnswerDraft(
        headline="Grounded answer",
        answer_text="",
        summary_points=[],
        caveats=[],
    )

    rendered = AnswerRenderer().render(payload, draft, citations, style=AnswerStyle.TECHNICAL)

    assert "Partially supported" in rendered.answer_text
    assert "claim-erbb2-higher" not in rendered.answer_text
    assert "[C" in rendered.answer_text


def test_markdown_renderer_outputs_expected_sections() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)
    draft = LLMAnswerDraft(headline="Grounded answer", answer_text="", summary_points=[], caveats=[])
    rendered = AnswerRenderer().render(payload, draft, citations, style=AnswerStyle.DETAILED)

    appendix = EvidenceAppendixRenderer().render(
        payload,
        citations,
        settings=Settings(_env_file=None, enable_optional_enrichment=False),
    )

    from answering.schemas.answer_models import ModelInfo
    from answering.services.response_packager import ResponsePackager

    final_payload = ResponsePackager().package(
        payload,
        rendered,
        citations,
        answer_style=AnswerStyle.DETAILED,
        model_info=ModelInfo(provider="fallback", model_name="template", temperature=0, fallback_used=True),
        evidence_appendix=appendix,
    )

    markdown = MarkdownRenderer().render(final_payload)

    assert "## Caveats" in markdown
    assert "## Citations" in markdown
    assert "Evidence-Backed Points" in markdown


def test_appendix_renderer_outputs_graph_and_gaps() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)

    appendix = EvidenceAppendixRenderer().render(
        payload,
        citations,
        settings=Settings(_env_file=None, enable_optional_enrichment=False),
    )

    assert appendix.graph_evidence_items
    assert appendix.unresolved_gaps
