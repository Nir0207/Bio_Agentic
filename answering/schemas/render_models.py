from __future__ import annotations

from pydantic import BaseModel, Field

from answering.schemas.answer_models import AnswerStyle, RenderedClaim


class PromptBundle(BaseModel):
    system_prompt: str
    user_prompt: str
    answer_style: AnswerStyle


class LLMAnswerDraft(BaseModel):
    headline: str
    answer_text: str
    summary_points: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class RenderedAnswer(BaseModel):
    headline: str
    answer_text: str
    summary_points: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    supported_claims: list[RenderedClaim] = Field(default_factory=list)
