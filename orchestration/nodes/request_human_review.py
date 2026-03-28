from __future__ import annotations

from langgraph.types import interrupt

from orchestration.app.config import Settings
from orchestration.app.constants import REVIEW_ACTION_CONTINUE, REVIEW_ACTION_EDIT, REVIEW_ACTION_REJECT
from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.schemas.evidence_models import EvidenceBundle
from orchestration.services.evidence_service import EvidenceService, ReviewPolicy


def request_human_review_node(
    state: OrchestrationState,
    *,
    settings: Settings,
    evidence_service: EvidenceService,
) -> dict:
    bundles = [bundle if isinstance(bundle, EvidenceBundle) else EvidenceBundle(**bundle) for bundle in (state.get("evidence_bundle") or [])]
    high_stakes = _is_high_stakes_query(state, settings)

    policy = ReviewPolicy(
        enabled=settings.enable_human_review,
        low_confidence_threshold=settings.hitl_low_confidence_threshold,
        min_citations=settings.hitl_min_citations,
        review_on_contradiction=settings.hitl_require_review_on_contradiction,
        review_high_stakes=settings.hitl_require_review_high_stakes,
    )

    needs_review, reason = evidence_service.review_decision(
        evidence_bundles=bundles,
        policy=policy,
        high_stakes=high_stakes,
    )

    if not needs_review:
        metadata = add_stage_metadata(
            state,
            "request_human_review",
            {"needs_review": False},
        )
        return {
            "needs_human_review": False,
            "review_reason": None,
            "execution_metadata": metadata,
        }

    review_payload = {
        "reason": reason,
        "instructions": "Provide {'action': 'continue'|'reject'|'edit', 'edits': {...optional...}}",
        "bundle_preview": [bundle.model_dump() for bundle in bundles[:3]],
    }
    decision = interrupt(review_payload)

    action, edits = _parse_decision(decision)
    updated_bundles = bundles
    errors = list(state.get("errors") or [])

    if action == REVIEW_ACTION_REJECT:
        errors.append(f"Human reviewer rejected payload (reason={reason})")
    elif action == REVIEW_ACTION_EDIT and edits:
        updated_bundles = _apply_edits_to_bundles(updated_bundles, edits)

    metadata = add_stage_metadata(
        state,
        "request_human_review",
        {
            "needs_review": True,
            "review_reason": reason,
            "review_action": action,
            "edit_keys": sorted(list(edits.keys())) if edits else [],
        },
    )

    return {
        "evidence_bundle": updated_bundles,
        "needs_human_review": False,
        "review_reason": reason,
        "errors": errors,
        "execution_metadata": metadata,
    }


def _parse_decision(decision: object) -> tuple[str, dict]:
    if isinstance(decision, str):
        normalized = decision.strip().lower()
        if normalized in {REVIEW_ACTION_CONTINUE, REVIEW_ACTION_REJECT, REVIEW_ACTION_EDIT}:
            return normalized, {}
        return REVIEW_ACTION_CONTINUE, {}

    if isinstance(decision, dict):
        action = str(decision.get("action", REVIEW_ACTION_CONTINUE)).strip().lower()
        if action not in {REVIEW_ACTION_CONTINUE, REVIEW_ACTION_REJECT, REVIEW_ACTION_EDIT}:
            action = REVIEW_ACTION_CONTINUE
        edits = decision.get("edits") if isinstance(decision.get("edits"), dict) else {}
        return action, edits

    return REVIEW_ACTION_CONTINUE, {}


def _apply_edits_to_bundles(bundles: list[EvidenceBundle], edits: dict) -> list[EvidenceBundle]:
    if not edits:
        return bundles

    updated: list[EvidenceBundle] = []
    bundle_edits = edits.get("bundles", {}) if isinstance(edits.get("bundles"), dict) else {}

    for bundle in bundles:
        edit_for_bundle = bundle_edits.get(bundle.candidate_id)
        if not isinstance(edit_for_bundle, dict):
            updated.append(bundle)
            continue

        warnings = list(bundle.warnings)
        unresolved_gaps = list(bundle.unresolved_gaps)

        if isinstance(edit_for_bundle.get("warnings"), list):
            warnings.extend(str(item) for item in edit_for_bundle["warnings"])
        if isinstance(edit_for_bundle.get("unresolved_gaps"), list):
            unresolved_gaps.extend(str(item) for item in edit_for_bundle["unresolved_gaps"])

        updated.append(
            bundle.model_copy(
                update={
                    "warnings": sorted(set(warnings)),
                    "unresolved_gaps": sorted(set(unresolved_gaps)),
                }
            )
        )

    return updated


def _is_high_stakes_query(state: OrchestrationState, settings: Settings) -> bool:
    metadata = dict(state.get("execution_metadata", {}))
    if metadata.get("high_stakes"):
        return True

    normalized_query = str(state.get("normalized_query") or state.get("user_query") or "").lower()
    return any(term.lower() in normalized_query for term in settings.hitl_high_stakes_terms)
