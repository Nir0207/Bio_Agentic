from __future__ import annotations

from datetime import datetime, timezone

from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import EvidenceBundle, GraphPath, ModelScore, ProvenanceRecord, SemanticHit
from orchestration.schemas.response_models import FinalPayload


def finalize_payload_node(state: OrchestrationState) -> dict:
    candidate_entities = [
        candidate if isinstance(candidate, CandidateEntity) else CandidateEntity(**candidate)
        for candidate in (state.get("candidate_entities") or [])
    ]
    graph_evidence = [
        evidence if isinstance(evidence, GraphPath) else GraphPath(**evidence)
        for evidence in (state.get("graph_evidence") or [])
    ]
    semantic_evidence = [
        evidence if isinstance(evidence, SemanticHit) else SemanticHit(**evidence)
        for evidence in (state.get("semantic_evidence") or [])
    ]
    model_scores = [
        score if isinstance(score, ModelScore) else ModelScore(**score)
        for score in (state.get("model_scores") or [])
    ]
    provenance = [
        row if isinstance(row, ProvenanceRecord) else ProvenanceRecord(**row)
        for row in (state.get("provenance") or [])
    ]
    evidence_bundle = [
        bundle if isinstance(bundle, EvidenceBundle) else EvidenceBundle(**bundle)
        for bundle in (state.get("evidence_bundle") or [])
    ]

    errors = [str(error) for error in (state.get("errors") or [])]
    needs_human_review = bool(state.get("needs_human_review"))
    review_reason = state.get("review_reason")

    if any("Human reviewer rejected" in error for error in errors):
        status = "rejected"
    elif needs_human_review:
        status = "review_required"
    elif errors:
        status = "completed_with_errors"
    else:
        status = "ready"

    confidence_summary = {
        bundle.candidate_id: bundle.confidence_summary for bundle in evidence_bundle
    }

    metadata = add_stage_metadata(
        state,
        "finalize_payload",
        {
            "status": status,
            "candidate_count": len(candidate_entities),
            "bundle_count": len(evidence_bundle),
        },
    )
    metadata["finished_at"] = datetime.now(timezone.utc).isoformat()

    payload = FinalPayload(
        user_query=str(state.get("user_query") or ""),
        normalized_query=str(state.get("normalized_query") or ""),
        intent_type=str(state.get("intent_type") or "evidence_lookup"),
        target_entity_ids=[str(item) for item in (state.get("target_entity_ids") or [])],
        candidate_entities=candidate_entities,
        graph_evidence=graph_evidence,
        semantic_evidence=semantic_evidence,
        model_scores=model_scores,
        provenance=provenance,
        confidence_summary=confidence_summary,
        evidence_bundle=evidence_bundle,
        needs_human_review=needs_human_review,
        review_reason=str(review_reason) if review_reason else None,
        status=status,
        errors=errors,
        execution_metadata=metadata,
    )

    return {
        "execution_metadata": metadata,
        "final_payload": payload.model_dump(),
    }
