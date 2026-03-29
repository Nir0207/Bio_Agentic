from __future__ import annotations

from orchestration.app.state import initialize_state


def test_initialize_state_has_required_keys() -> None:
    state = initialize_state("prioritize EGFR", high_stakes=True)

    assert state["user_query"] == "prioritize EGFR"
    assert state["normalized_query"] == ""
    assert state["intent_type"] == "evidence_lookup"
    assert state["target_entity_ids"] == []
    assert state["candidate_entities"] == []
    assert state["graph_evidence"] == []
    assert state["semantic_evidence"] == []
    assert state["model_scores"] == []
    assert state["provenance"] == []
    assert state["evidence_bundle"] == []
    assert state["final_payload"] == {}
    assert state["errors"] == []
    assert state["execution_metadata"]["high_stakes"] is True
