from __future__ import annotations

from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import ModelScore
from orchestration.tools.scoring_tools import ModelScoreRequest, ScoringTools


def fetch_scores_node(state: OrchestrationState, *, scoring_tools: ScoringTools) -> dict:
    candidate_entities = list(state.get("candidate_entities") or [])
    target_entity_ids = list(state.get("target_entity_ids") or [])

    candidate_ids: set[str] = set(target_entity_ids)
    for candidate in candidate_entities:
        if isinstance(candidate, CandidateEntity):
            candidate_ids.add(candidate.candidate_id)
        else:
            candidate_ids.add(str(candidate.get("candidate_id")))

    model_scores: list[ModelScore] = []
    metadata = dict(state.get("execution_metadata", {}))
    tool_runs = list(metadata.get("tool_runs", []))

    for candidate_id in sorted(candidate_ids):
        if not candidate_id:
            continue
        result = scoring_tools.get_model_score(ModelScoreRequest(candidate_id=candidate_id))
        tool_runs.append(result.execution_metadata.model_dump())
        if result.model_score is not None:
            model_scores.append(result.model_score)

    model_scores.sort(key=lambda item: (-item.score_value, item.candidate_id))

    metadata["tool_runs"] = tool_runs
    metadata = add_stage_metadata(
        {**state, "execution_metadata": metadata},
        "fetch_scores",
        {
            "scored_candidate_count": len(model_scores),
        },
    )

    return {
        "model_scores": model_scores,
        "execution_metadata": metadata,
    }
