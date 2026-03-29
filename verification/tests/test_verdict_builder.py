from __future__ import annotations

import json
from pathlib import Path

from verification.app.config import Settings
from verification.services.claim_extractor import ClaimExtractor
from verification.services.citation_verifier import CitationVerifier
from verification.services.graph_verifier import GraphVerifier
from verification.services.score_verifier import ScoreVerifier
from verification.services.verdict_builder import VerdictBuilder
from verification.schemas.evidence_models import VerificationInputPayload


def _load_sample_payload() -> VerificationInputPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_orchestration_payload.json"
    return VerificationInputPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_verdict_builder_aggregates_claim_checks() -> None:
    payload = _load_sample_payload()
    claims = ClaimExtractor().extract_claims(payload)

    graph_checks = GraphVerifier().verify_claims(claims, payload)
    citation_checks = CitationVerifier().verify_claims(claims, payload)
    score_checks = ScoreVerifier().verify_claims(claims, payload)

    settings = Settings(
        _env_file=None,
        enable_human_review=True,
        low_confidence_threshold=0.45,
        min_citations_per_claim=1,
        review_on_contradiction=True,
    )

    computation = VerdictBuilder().build(
        payload=payload,
        claims=claims,
        graph_checks=graph_checks,
        citation_checks=citation_checks,
        score_checks=score_checks,
        settings=settings,
    )

    assert computation.claim_verdicts
    assert computation.confidence_summary.overall_confidence >= 0
    assert computation.overall_verdict.value in {"approved", "approved_with_caveats", "review_required", "rejected"}


def test_score_consistency_for_ranking_claim_is_not_false_when_order_matches() -> None:
    payload = _load_sample_payload()
    claims = ClaimExtractor().extract_claims(payload)
    ranking_claims = [claim for claim in claims if claim.claim_type.value == "ranking_claim"]

    assert ranking_claims

    score_checks = ScoreVerifier().verify_claims(ranking_claims, payload)
    assert score_checks
    assert all(check.score_supported in {"true", "partial"} for check in score_checks)
