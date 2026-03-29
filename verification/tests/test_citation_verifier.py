from __future__ import annotations

import json
from pathlib import Path

from verification.schemas.claim_models import ClaimType, DirectnessLevel, ExtractedClaim
from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.citation_verifier import CitationVerifier


def _load_sample_payload() -> VerificationInputPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_orchestration_payload.json"
    return VerificationInputPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_citation_verifier_resolves_citations_for_supported_claim() -> None:
    payload = _load_sample_payload()
    claim = ExtractedClaim(
        claim_id="claim-001",
        claim_text="EGFR participates in MAPK signaling supported by PMID:12345.",
        claim_type=ClaimType.PATHWAY_PARTICIPATION,
        target_entity_ids=["EGFR"],
        directness_level=DirectnessLevel.UNSPECIFIED,
        referenced_citation_ids=["PMID:12345"],
    )

    result = CitationVerifier().verify_claims([claim], payload)[0]

    assert result.citation_supported in {"true", "partial"}
    assert "PMID:12345" in result.supporting_citation_ids


def test_citation_verifier_flags_missing_citation_coverage() -> None:
    payload = _load_sample_payload().model_copy(update={"semantic_evidence": [], "provenance": []})
    claim = ExtractedClaim(
        claim_id="claim-002",
        claim_text="ERBB2 has strong evidence support.",
        claim_type=ClaimType.EVIDENCE_STRENGTH_CLAIM,
        target_entity_ids=["ERBB2"],
        directness_level=DirectnessLevel.UNSPECIFIED,
    )

    result = CitationVerifier().verify_claims([claim], payload)[0]

    assert result.citation_supported == "false"
    assert result.missing_citation_reason
