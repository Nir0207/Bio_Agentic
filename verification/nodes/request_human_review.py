from __future__ import annotations

from typing import Any

from verification.app.constants import (
    ALLOWED_REVIEW_ACTIONS,
    REVIEW_ACTION_APPROVE,
    REVIEW_ACTION_CONTINUE_WITH_CAVEATS,
    REVIEW_ACTION_EDIT,
    REVIEW_ACTION_REJECT,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_CONTINUED_WITH_CAVEATS,
    REVIEW_STATUS_EDITED,
    REVIEW_STATUS_NOT_REQUIRED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_REJECTED,
    VERDICT_APPROVED,
    VERDICT_APPROVED_WITH_CAVEATS,
    VERDICT_REJECTED,
)
from verification.app.state import VerificationState
from verification.schemas.verification_models import ClaimFinalStatus, HumanReviewStatus


def request_human_review_node(
    state: VerificationState,
    *,
    enable_human_review: bool,
    review_action: str | None = None,
    review_edits: dict[str, Any] | None = None,
) -> dict:
    claim_verdicts = list(state.get("claim_verdicts") or [])
    review_required = bool(state.get("review_required"))
    review_reasons = list(state.get("review_reasons") or [])

    pending_claim_ids = [
        verdict.claim.claim_id
        for verdict in claim_verdicts
        if verdict.final_status in {ClaimFinalStatus.UNSUPPORTED, ClaimFinalStatus.NEEDS_REVIEW}
    ]

    if not enable_human_review or not review_required:
        return {
            "review_status": HumanReviewStatus(
                status=REVIEW_STATUS_NOT_REQUIRED,
                triggered=False,
                reasons=[],
                pending_claim_ids=[],
                allowed_actions=[],
            )
        }

    action = (review_action or "").strip().lower() or None
    edits = review_edits if isinstance(review_edits, dict) else {}

    if action is None:
        return {
            "review_status": HumanReviewStatus(
                status=REVIEW_STATUS_PENDING,
                triggered=True,
                reasons=review_reasons,
                pending_claim_ids=pending_claim_ids,
                allowed_actions=sorted(ALLOWED_REVIEW_ACTIONS),
            )
        }

    if action not in ALLOWED_REVIEW_ACTIONS:
        return {
            "review_status": HumanReviewStatus(
                status=REVIEW_STATUS_PENDING,
                triggered=True,
                reasons=review_reasons + [f"Unknown review action: {action}"],
                pending_claim_ids=pending_claim_ids,
                allowed_actions=sorted(ALLOWED_REVIEW_ACTIONS),
            )
        }

    update: dict[str, Any] = {}

    if action == REVIEW_ACTION_APPROVE:
        if str(state.get("overall_verdict")) == VERDICT_REJECTED:
            update["overall_verdict"] = VERDICT_APPROVED_WITH_CAVEATS
        else:
            update["overall_verdict"] = VERDICT_APPROVED

        update["review_status"] = HumanReviewStatus(
            status=REVIEW_STATUS_APPROVED,
            triggered=True,
            reasons=review_reasons,
            pending_claim_ids=pending_claim_ids,
            allowed_actions=sorted(ALLOWED_REVIEW_ACTIONS),
            action_taken=REVIEW_ACTION_APPROVE,
        )
        return update

    if action == REVIEW_ACTION_REJECT:
        update["overall_verdict"] = VERDICT_REJECTED
        update["review_status"] = HumanReviewStatus(
            status=REVIEW_STATUS_REJECTED,
            triggered=True,
            reasons=review_reasons,
            pending_claim_ids=pending_claim_ids,
            allowed_actions=sorted(ALLOWED_REVIEW_ACTIONS),
            action_taken=REVIEW_ACTION_REJECT,
        )
        return update

    if action == REVIEW_ACTION_CONTINUE_WITH_CAVEATS:
        update["overall_verdict"] = VERDICT_APPROVED_WITH_CAVEATS
        update["review_status"] = HumanReviewStatus(
            status=REVIEW_STATUS_CONTINUED_WITH_CAVEATS,
            triggered=True,
            reasons=review_reasons,
            pending_claim_ids=pending_claim_ids,
            allowed_actions=sorted(ALLOWED_REVIEW_ACTIONS),
            action_taken=REVIEW_ACTION_CONTINUE_WITH_CAVEATS,
        )
        return update

    if action == REVIEW_ACTION_EDIT:
        claim_overrides = edits.get("claim_status_overrides") if isinstance(edits.get("claim_status_overrides"), dict) else {}

        updated_verdicts = []
        for verdict in claim_verdicts:
            status_override = claim_overrides.get(verdict.claim.claim_id)
            if status_override in {member.value for member in ClaimFinalStatus}:
                updated_verdicts.append(verdict.model_copy(update={"final_status": status_override}))
            else:
                updated_verdicts.append(verdict)

        update["claim_verdicts"] = updated_verdicts
        update["overall_verdict"] = VERDICT_APPROVED_WITH_CAVEATS
        update["review_status"] = HumanReviewStatus(
            status=REVIEW_STATUS_EDITED,
            triggered=True,
            reasons=review_reasons,
            pending_claim_ids=pending_claim_ids,
            allowed_actions=sorted(ALLOWED_REVIEW_ACTIONS),
            action_taken=REVIEW_ACTION_EDIT,
            edits_applied=edits,
        )
        return update

    return {}
