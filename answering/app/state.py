from __future__ import annotations

from typing import TypedDict

from answering.schemas.answer_models import FinalAnswerPayload
from answering.schemas.citation_models import CitationMap
from answering.schemas.render_models import LLMAnswerDraft, PromptBundle, RenderedAnswer
from answering.schemas.verified_payload_models import VerifiedPayload


class AnsweringState(TypedDict, total=False):
    verified_payload: VerifiedPayload
    citations: CitationMap
    prompt_bundle: PromptBundle
    llm_draft: LLMAnswerDraft
    rendered_answer: RenderedAnswer
    final_payload: FinalAnswerPayload
