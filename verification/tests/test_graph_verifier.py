from __future__ import annotations

import json
from pathlib import Path

from verification.schemas.claim_models import ClaimType, DirectnessLevel, ExtractedClaim
from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.graph_verifier import GraphVerifier


def _load_sample_payload() -> VerificationInputPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_orchestration_payload.json"
    return VerificationInputPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_graph_verifier_finds_pathway_support() -> None:
    payload = _load_sample_payload()
    claim = ExtractedClaim(
        claim_id="claim-001",
        claim_text="EGFR participates in MAPK signaling.",
        claim_type=ClaimType.PATHWAY_PARTICIPATION,
        target_entity_ids=["EGFR"],
        directness_level=DirectnessLevel.DIRECT,
    )

    result = GraphVerifier().verify_claims([claim], payload)[0]

    assert result.graph_supported in {"true", "partial"}
    assert result.path_count >= 1
    assert result.supporting_graph_evidence_ids


def test_graph_verifier_marks_missing_target_as_unsupported() -> None:
    payload = _load_sample_payload()
    claim = ExtractedClaim(
        claim_id="claim-xyz",
        claim_text="UNKNOWN1 directly interacts with UNKNOWN2.",
        claim_type=ClaimType.ENTITY_ASSOCIATION,
        target_entity_ids=["UNKNOWN1", "UNKNOWN2"],
        directness_level=DirectnessLevel.DIRECT,
    )

    result = GraphVerifier().verify_claims([claim], payload)[0]

    assert result.graph_supported == "false"
    assert result.unsupported_reason
