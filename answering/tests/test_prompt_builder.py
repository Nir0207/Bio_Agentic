from __future__ import annotations

import json
from pathlib import Path

from answering.schemas.answer_models import AnswerStyle
from answering.schemas.verified_payload_models import VerifiedPayload
from answering.services.citation_formatter import CitationFormatter
from answering.services.prompt_builder import PromptBuilder


def _sample_payload() -> VerifiedPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_verified_payload.json"
    return VerifiedPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_prompt_builder_excludes_unsupported_claims() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)

    prompt_bundle = PromptBuilder().build(payload, citations, style=AnswerStyle.TECHNICAL)

    assert "claim-erbb2-higher" not in prompt_bundle.user_prompt
    assert "claim-egfr-mapk" in prompt_bundle.user_prompt
    assert "claim-egfr-erbb2" in prompt_bundle.user_prompt


def test_prompt_builder_includes_citation_tags_for_supported_claims() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)

    prompt_bundle = PromptBuilder().build(payload, citations, style=AnswerStyle.DETAILED)

    assert "citation_tags" in prompt_bundle.user_prompt
    assert "[C1]" in prompt_bundle.user_prompt
