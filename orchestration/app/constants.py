from __future__ import annotations

from typing import Final

INTENT_TYPES: Final[tuple[str, ...]] = (
    "target_prioritization",
    "pathway_exploration",
    "evidence_lookup",
    "similarity_lookup",
)

DEFAULT_INTENT: Final[str] = "evidence_lookup"

DEFAULT_GRAPH_TOP_K: Final[int] = 5
DEFAULT_SEMANTIC_TOP_K: Final[int] = 5
DEFAULT_MAX_GRAPH_HOPS: Final[int] = 2
DEFAULT_MAX_GRAPH_PATHS: Final[int] = 4

CANDIDATE_WEIGHT_GRAPH: Final[float] = 0.40
CANDIDATE_WEIGHT_SEMANTIC: Final[float] = 0.25
CANDIDATE_WEIGHT_MODEL: Final[float] = 0.35

HITL_REASON_LOW_CONFIDENCE: Final[str] = "low_confidence_evidence_bundle"
HITL_REASON_CONTRADICTORY: Final[str] = "contradictory_signals"
HITL_REASON_LOW_CITATIONS: Final[str] = "too_few_citations"
HITL_REASON_HIGH_STAKES: Final[str] = "high_stakes_request"

REVIEW_ACTION_CONTINUE: Final[str] = "continue"
REVIEW_ACTION_REJECT: Final[str] = "reject"
REVIEW_ACTION_EDIT: Final[str] = "edit"

SCORE_PROPERTY_DEFAULTS: Final[dict[str, str]] = {
    "score": "target_score",
    "model_name": "target_score_model_name",
    "model_version": "target_score_model_version",
    "run_id": "target_score_run_id",
    "timestamp": "target_score_created_at",
}
