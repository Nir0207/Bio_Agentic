from __future__ import annotations

from pathlib import Path

FINAL_VERIFIED_PAYLOAD_VERSION = "1.0.0"
DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.60
DEFAULT_MIN_CITATIONS_PER_CLAIM = 1

REVIEW_ACTION_APPROVE = "approve"
REVIEW_ACTION_REJECT = "reject"
REVIEW_ACTION_EDIT = "edit"
REVIEW_ACTION_CONTINUE_WITH_CAVEATS = "continue_with_caveats"
ALLOWED_REVIEW_ACTIONS = {
    REVIEW_ACTION_APPROVE,
    REVIEW_ACTION_REJECT,
    REVIEW_ACTION_EDIT,
    REVIEW_ACTION_CONTINUE_WITH_CAVEATS,
}

CLAIM_STATUS_SUPPORTED = "supported"
CLAIM_STATUS_PARTIALLY_SUPPORTED = "partially_supported"
CLAIM_STATUS_UNSUPPORTED = "unsupported"
CLAIM_STATUS_NEEDS_REVIEW = "needs_review"

VERDICT_APPROVED = "approved"
VERDICT_APPROVED_WITH_CAVEATS = "approved_with_caveats"
VERDICT_REVIEW_REQUIRED = "review_required"
VERDICT_REJECTED = "rejected"

REVIEW_STATUS_NOT_REQUIRED = "not_required"
REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_REJECTED = "rejected"
REVIEW_STATUS_EDITED = "edited"
REVIEW_STATUS_CONTINUED_WITH_CAVEATS = "continued_with_caveats"

HIGH_STAKES_TERMS = [
    "dose",
    "toxicity",
    "contraindication",
    "life-threatening",
    "critical",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_SAMPLE_PAYLOAD_PATH = PACKAGE_ROOT / "payloads" / "sample_orchestration_payload.json"
