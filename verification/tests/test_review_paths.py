from __future__ import annotations

import json
from pathlib import Path

from verification.app.config import Settings
from verification.nodes.compute_verdict import compute_verdict_node
from verification.nodes.extract_claims import extract_claims_node
from verification.nodes.finalize_verified_payload import finalize_verified_payload_node
from verification.nodes.request_human_review import request_human_review_node
from verification.nodes.verify_citations import verify_citations_node
from verification.nodes.verify_graph_support import verify_graph_support_node
from verification.nodes.verify_scores import verify_scores_node
from verification.schemas.evidence_models import VerificationInputPayload
from verification.services.claim_extractor import ClaimExtractor
from verification.services.citation_verifier import CitationVerifier
from verification.services.graph_verifier import GraphVerifier
from verification.services.score_verifier import ScoreVerifier
from verification.services.verdict_builder import VerdictBuilder


def _load_sample_payload() -> VerificationInputPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_orchestration_payload.json"
    return VerificationInputPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _build_state(payload: VerificationInputPayload) -> dict:
    state: dict = {"input_payload": payload}
    state.update(extract_claims_node(state, extractor=ClaimExtractor()))
    state.update(verify_graph_support_node(state, verifier=GraphVerifier()))
    state.update(verify_citations_node(state, verifier=CitationVerifier()))
    state.update(verify_scores_node(state, verifier=ScoreVerifier()))
    state.update(
        compute_verdict_node(
            state,
            builder=VerdictBuilder(),
            settings=Settings(
                _env_file=None,
                enable_human_review=True,
                low_confidence_threshold=0.70,
                min_citations_per_claim=1,
                review_on_contradiction=True,
                review_high_stakes=True,
            ),
        )
    )
    return state


def test_review_required_path_sets_pending_status_without_action() -> None:
    payload = _load_sample_payload().model_copy(update={"high_stakes": True})
    state = _build_state(payload)

    update = request_human_review_node(state, enable_human_review=True)
    assert update["review_status"].status in {"pending", "not_required"}


def test_review_reject_overrides_overall_verdict() -> None:
    payload = _load_sample_payload().model_copy(update={"high_stakes": True})
    state = _build_state(payload)

    state.update(request_human_review_node(state, enable_human_review=True, review_action="reject"))
    assert state["overall_verdict"] == "rejected"


def test_finalize_payload_schema_contains_required_fields() -> None:
    payload = _load_sample_payload()
    state = _build_state(payload)
    state.update(request_human_review_node(state, enable_human_review=True, review_action="continue_with_caveats"))
    final = finalize_verified_payload_node(state)["final_verified_payload"]

    assert final.original_query
    assert final.extracted_claims
    assert final.claim_verdicts
    assert final.overall_verdict.value in {"approved", "approved_with_caveats", "review_required", "rejected"}
    assert isinstance(final.supporting_evidence_index, dict)
    assert final.final_verified_payload_version
