from __future__ import annotations

import uuid

from langgraph.types import Command

from orchestration.app.state import initialize_state


def test_interrupt_triggered_for_high_stakes(graph) -> None:
    config = {"configurable": {"thread_id": f"t-{uuid.uuid4().hex[:8]}"}}
    result = graph.invoke(initialize_state("Dose critical EGFR question", high_stakes=True), config=config)

    assert "__interrupt__" in result


def test_interrupt_resume_continue_reaches_final_payload(graph) -> None:
    config = {"configurable": {"thread_id": f"t-{uuid.uuid4().hex[:8]}"}}
    first = graph.invoke(initialize_state("Dose critical EGFR question", high_stakes=True), config=config)
    assert "__interrupt__" in first

    resumed = graph.invoke(Command(resume={"action": "continue"}), config=config)
    assert "final_payload" in resumed
    assert resumed["final_payload"]["status"] in {"ready", "completed_with_errors"}


def test_interrupt_resume_reject_sets_rejected_status(graph) -> None:
    config = {"configurable": {"thread_id": f"t-{uuid.uuid4().hex[:8]}"}}
    first = graph.invoke(initialize_state("Dose critical EGFR question", high_stakes=True), config=config)
    assert "__interrupt__" in first

    resumed = graph.invoke(Command(resume={"action": "reject"}), config=config)
    assert resumed["final_payload"]["status"] == "rejected"
    assert resumed["final_payload"]["errors"]
