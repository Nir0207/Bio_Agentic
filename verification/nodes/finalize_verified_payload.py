from __future__ import annotations

from verification.app.constants import FINAL_VERIFIED_PAYLOAD_VERSION
from verification.app.state import VerificationState
from verification.schemas.evidence_models import VerificationInputPayload
from verification.schemas.verification_models import HumanReviewStatus, VerifiedPayload


def finalize_verified_payload_node(state: VerificationState) -> dict:
    payload = state.get("input_payload")
    if not isinstance(payload, VerificationInputPayload):
        payload = VerificationInputPayload.model_validate(payload or {})

    extracted_claims = list(state.get("extracted_claims") or [])
    claim_verdicts = list(state.get("claim_verdicts") or [])

    confidence_summary = state.get("confidence_summary")
    if confidence_summary is None:
        raise ValueError("Missing confidence_summary in verification state")

    review_status = state.get("review_status")
    if not isinstance(review_status, HumanReviewStatus):
        review_status = HumanReviewStatus.model_validate(review_status or {})

    unsupported_claims = [
        verdict.claim.claim_id
        for verdict in claim_verdicts
        if verdict.final_status.value == "unsupported"
    ]

    missing_citations = [
        verdict.claim.claim_id
        for verdict in claim_verdicts
        if verdict.citation_check.citation_supported in {"false", "partial"}
    ]

    supporting_index: dict[str, list[str]] = {}
    missing_index: dict[str, list[str]] = {}

    for verdict in claim_verdicts:
        claim_id = verdict.claim.claim_id
        supporting = sorted(
            set(
                verdict.graph_check.supporting_graph_evidence_ids
                + verdict.citation_check.supporting_citation_ids
                + [f"{block.get('candidate_id')}:{block.get('score_name')}" for block in verdict.score_check.supporting_score_blocks]
            )
        )
        supporting_index[claim_id] = [item for item in supporting if item and item != "None:None"]

        missing_bits: list[str] = []
        if verdict.graph_check.graph_supported == "false":
            missing_bits.append("graph_support")
        if verdict.citation_check.citation_supported in {"false", "partial"}:
            missing_bits.append("citation_support")
        if verdict.score_check.score_supported == "false":
            missing_bits.append("score_support")
        missing_index[claim_id] = missing_bits

    final_payload = VerifiedPayload(
        original_query=payload.original_query,
        candidate_entities=payload.candidate_entities,
        extracted_claims=extracted_claims,
        claim_verdicts=claim_verdicts,
        unsupported_claims=unsupported_claims,
        missing_citations=missing_citations,
        overall_verdict=str(state.get("overall_verdict") or "review_required"),
        overall_confidence=confidence_summary.overall_confidence,
        confidence_summary=confidence_summary,
        supporting_evidence_index=supporting_index,
        missing_evidence_index=missing_index,
        warnings=list(state.get("warnings") or []),
        review_status=review_status,
        final_verified_payload_version=FINAL_VERIFIED_PAYLOAD_VERSION,
    )

    return {
        "final_verified_payload": final_payload,
    }
