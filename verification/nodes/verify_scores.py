from __future__ import annotations

from verification.app.state import VerificationState
from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.score_verifier import ScoreVerifier


def verify_scores_node(state: VerificationState, *, verifier: ScoreVerifier) -> dict:
    payload = state.get("input_payload")
    if not isinstance(payload, VerificationInputPayload):
        payload = VerificationInputPayload.model_validate(payload or {})

    claims = list(state.get("extracted_claims") or [])
    checks = verifier.verify_claims(claims, payload)
    return {"score_checks": checks}
