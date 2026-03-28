from __future__ import annotations

from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import GraphPath, ModelScore, SemanticHit
from orchestration.services.evidence_service import EvidenceService


def assemble_candidates_node(state: OrchestrationState, *, evidence_service: EvidenceService) -> dict:
    graph_paths = list(state.get("graph_evidence") or [])
    semantic_hits = list(state.get("semantic_evidence") or [])
    model_scores = list(state.get("model_scores") or [])

    graph_candidates = _coerce_candidates(state.get("candidate_entities") or [])

    # Keep candidate graph support deterministic from retrieved graph evidence.
    by_id = {candidate.candidate_id: candidate for candidate in graph_candidates}
    for path in graph_paths:
        graph_path = path if isinstance(path, GraphPath) else GraphPath(**path)
        candidate = by_id.get(graph_path.candidate_id)
        if candidate is None:
            candidate = CandidateEntity(
                candidate_id=graph_path.candidate_id,
                candidate_type=graph_path.candidate_type,
                display_name=graph_path.nodes[0].display_name if graph_path.nodes else graph_path.candidate_id,
                sources=["graph"],
            )
            by_id[candidate.candidate_id] = candidate
        candidate.graph_support = max(candidate.graph_support, float(graph_path.confidence or 0.0))

    merged = evidence_service.merge_candidates(
        graph_candidates=list(by_id.values()),
        semantic_hits=[hit if isinstance(hit, SemanticHit) else SemanticHit(**hit) for hit in semantic_hits],
        model_scores=[score if isinstance(score, ModelScore) else ModelScore(**score) for score in model_scores],
    )

    metadata = add_stage_metadata(
        state,
        "assemble_candidates",
        {
            "candidate_count": len(merged),
            "top_candidate": merged[0].candidate_id if merged else None,
        },
    )

    return {
        "candidate_entities": merged,
        "execution_metadata": metadata,
    }


def _coerce_candidates(candidates: list[CandidateEntity | dict]) -> list[CandidateEntity]:
    output: list[CandidateEntity] = []
    for candidate in candidates:
        if isinstance(candidate, CandidateEntity):
            output.append(candidate)
        else:
            output.append(CandidateEntity(**candidate))
    return output
