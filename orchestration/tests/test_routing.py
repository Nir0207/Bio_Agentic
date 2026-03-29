from __future__ import annotations

from orchestration.app.state import initialize_state
from orchestration.nodes.route_query import route_query_node


def test_route_query_classifies_target_prioritization() -> None:
    state = initialize_state("Prioritize EGFR and ALK for lung cancer")
    update = route_query_node(state)

    assert update["intent_type"] == "target_prioritization"
    assert "EGFR" in update["target_entity_ids"]
    assert "ALK" in update["target_entity_ids"]


def test_route_query_classifies_similarity_lookup() -> None:
    state = initialize_state("Find similar proteins to EGFR")
    update = route_query_node(state)

    assert update["intent_type"] == "similarity_lookup"


def test_route_query_defaults_when_no_rule_match() -> None:
    state = initialize_state("What do we have")
    update = route_query_node(state)

    assert update["intent_type"] == "evidence_lookup"
