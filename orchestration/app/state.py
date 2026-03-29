from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict

from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import EvidenceBundle, GraphPath, ModelScore, ProvenanceRecord, SemanticHit


class OrchestrationState(TypedDict, total=False):
    user_query: str
    normalized_query: str
    intent_type: str
    target_entity_ids: list[str]
    candidate_entities: list[CandidateEntity]
    graph_evidence: list[GraphPath]
    semantic_evidence: list[SemanticHit]
    model_scores: list[ModelScore]
    provenance: list[ProvenanceRecord]
    needs_human_review: bool
    review_reason: str | None
    evidence_bundle: list[EvidenceBundle]
    final_payload: dict[str, Any]
    errors: list[str]
    execution_metadata: dict[str, Any]


def initialize_state(user_query: str, *, high_stakes: bool = False) -> OrchestrationState:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "user_query": user_query,
        "normalized_query": "",
        "intent_type": "evidence_lookup",
        "target_entity_ids": [],
        "candidate_entities": [],
        "graph_evidence": [],
        "semantic_evidence": [],
        "model_scores": [],
        "provenance": [],
        "needs_human_review": False,
        "review_reason": None,
        "evidence_bundle": [],
        "final_payload": {},
        "errors": [],
        "execution_metadata": {
            "started_at": now,
            "high_stakes": high_stakes,
            "stages": [],
            "tool_runs": [],
        },
    }


def add_stage_metadata(state: OrchestrationState, stage: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = dict(state.get("execution_metadata", {}))
    stages = list(metadata.get("stages", []))
    stages.append(
        {
            "stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
    )
    metadata["stages"] = stages
    return metadata


def add_error(state: OrchestrationState, message: str) -> dict[str, list[str]]:
    errors = list(state.get("errors", []))
    errors.append(message)
    return {"errors": errors}
