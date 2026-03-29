from __future__ import annotations

import json
from pathlib import Path

from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.claim_extractor import ClaimExtractor


def _load_sample_payload() -> VerificationInputPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_orchestration_payload.json"
    return VerificationInputPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_claim_extraction_returns_structured_claims() -> None:
    payload = _load_sample_payload()
    claims = ClaimExtractor().extract_claims(payload)

    assert claims
    assert all(claim.claim_id.startswith("claim-") for claim in claims)
    assert all(claim.claim_text for claim in claims)
    assert all(claim.claim_type.value for claim in claims)
    assert all(claim.target_entity_ids for claim in claims)
    assert any(claim.source_span is not None for claim in claims)


def test_claim_extraction_without_draft_uses_evidence_summaries() -> None:
    payload = _load_sample_payload().model_copy(update={"draft_answer_text": None})
    claims = ClaimExtractor().extract_claims(payload)

    assert claims
    assert all(claim.source_span is None for claim in claims)
