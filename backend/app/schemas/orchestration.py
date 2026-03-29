from pydantic import BaseModel


class OrchestrationPayload(BaseModel):
    query: str
    candidates: list[dict]
    evidence_bundle: list[dict]
    metadata: dict


class OrchestrationResponse(BaseModel):
    payload: OrchestrationPayload
