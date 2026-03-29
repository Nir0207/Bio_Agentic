from pydantic import BaseModel, Field


class VerificationRequest(BaseModel):
    query: str | None = None
    orchestration_payload: dict | None = None


class ClaimResult(BaseModel):
    claim: str
    status: str
    confidence: float = Field(..., ge=0, le=1)
    citations: list[str]


class VerificationPayload(BaseModel):
    overall_verdict: str
    overall_confidence: float = Field(..., ge=0, le=1)
    claims: list[ClaimResult]
    warnings: list[str]
    citations: list[str]


class VerificationResponse(BaseModel):
    payload: VerificationPayload
