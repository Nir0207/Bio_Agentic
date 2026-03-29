from __future__ import annotations

from verification.app.config import Settings
from verification.app.state import VerificationState
from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.verdict_builder import VerdictBuilder


def compute_verdict_node(
    state: VerificationState,
    *,
    builder: VerdictBuilder,
    settings: Settings,
) -> dict:
    payload = state.get("input_payload")
    if not isinstance(payload, VerificationInputPayload):
        payload = VerificationInputPayload.model_validate(payload or {})

    claims = list(state.get("extracted_claims") or [])
    graph_checks = list(state.get("graph_checks") or [])
    citation_checks = list(state.get("citation_checks") or [])
    score_checks = list(state.get("score_checks") or [])

    computation = builder.build(
        payload=payload,
        claims=claims,
        graph_checks=graph_checks,
        citation_checks=citation_checks,
        score_checks=score_checks,
        settings=settings,
    )

    return {
        "claim_verdicts": computation.claim_verdicts,
        "overall_verdict": computation.overall_verdict.value,
        "confidence_summary": computation.confidence_summary,
        "warnings": computation.warnings,
        "review_required": computation.review_required,
        "review_reasons": computation.review_reasons,
    }
