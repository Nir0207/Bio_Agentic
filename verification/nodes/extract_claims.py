from __future__ import annotations

from verification.app.state import VerificationState
from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.claim_extractor import ClaimExtractor


def extract_claims_node(state: VerificationState, *, extractor: ClaimExtractor) -> dict:
    payload = state.get("input_payload")
    if not isinstance(payload, VerificationInputPayload):
        payload = VerificationInputPayload.model_validate(payload or {})

    claims = extractor.extract_claims(payload)
    return {
        "input_payload": payload,
        "extracted_claims": claims,
    }
