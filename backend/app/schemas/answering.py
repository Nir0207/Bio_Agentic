from pydantic import BaseModel, Field


class AnsweringRequest(BaseModel):
    query: str | None = None
    verified_payload: dict | None = None
    style: str = 'concise'


class AnsweringPayload(BaseModel):
    answer_text: str
    verdict: str
    confidence: float = Field(..., ge=0, le=1)
    citations: list[str]
    evidence_appendix: list[str]
    style: str


class AnsweringResponse(BaseModel):
    payload: AnsweringPayload
