from __future__ import annotations

from verification.app.state import VerificationState
from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.graph_verifier import GraphVerifier


def verify_graph_support_node(state: VerificationState, *, verifier: GraphVerifier) -> dict:
    payload = state.get("input_payload")
    if not isinstance(payload, VerificationInputPayload):
        payload = VerificationInputPayload.model_validate(payload or {})

    claims = list(state.get("extracted_claims") or [])
    checks = verifier.verify_claims(claims, payload)
    return {"graph_checks": checks}
