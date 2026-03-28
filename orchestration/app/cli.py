from __future__ import annotations

import json
import uuid
from typing import Any

import typer
from langgraph.types import Command

from orchestration.app.config import get_settings
from orchestration.app.graph_builder import build_graph, build_runtime, verify_upstream_dependencies
from orchestration.app.logging import configure_logging
from orchestration.app.state import initialize_state
from orchestration.tools.evidence_tools import ProvenanceRequest
from orchestration.tools.neo4j_tools import PathwayContextRequest, SimilarEntitiesRequest, SubgraphRequest
from orchestration.tools.scoring_tools import ModelScoreRequest
from orchestration.tools.semantic_search_tools import EvidenceSearchRequest, PublicationSearchRequest

app = typer.Typer(add_completion=False, help="LangGraph orchestration phase for graph + semantic + score evidence assembly.")
run_app = typer.Typer(add_completion=False)
app.add_typer(run_app, name="run")


@run_app.command("query")
def run_query(
    text: str = typer.Option(..., "--text"),
    high_stakes: bool = typer.Option(False, "--high-stakes"),
    review_action: str | None = typer.Option(None, "--review-action"),
    review_edits: str | None = typer.Option(None, "--review-edits"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    graph, runtime = build_graph(runtime=build_runtime(settings))
    try:
        payload = _run_graph_with_optional_resume(
            graph=graph,
            text=text,
            high_stakes=high_stakes,
            review_action=review_action,
            review_edits=review_edits,
        )
        typer.echo(json.dumps(payload, indent=2))
    finally:
        runtime.close()


@run_app.command("sample")
def run_sample(
    review_action: str | None = typer.Option(None, "--review-action"),
    review_edits: str | None = typer.Option(None, "--review-edits"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    graph, runtime = build_graph(runtime=build_runtime(settings))
    try:
        payload = _run_graph_with_optional_resume(
            graph=graph,
            text=settings.sample_query,
            high_stakes=False,
            review_action=review_action,
            review_edits=review_edits,
        )
        typer.echo(json.dumps(payload, indent=2))
    finally:
        runtime.close()


@run_app.command("all")
def run_all(
    review_action: str | None = typer.Option(None, "--review-action"),
    review_edits: str | None = typer.Option(None, "--review-edits"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    runtime = build_runtime(settings)
    dependency_report = verify_upstream_dependencies(runtime)

    graph, runtime = build_graph(runtime=runtime)
    try:
        result = {
            "dependency_report": {
                "neo4j_connectivity": dependency_report.neo4j_connectivity,
                "upstream_directories": dependency_report.upstream_directories,
                "modeling_artifacts_root": dependency_report.modeling_artifacts_root,
            }
        }
        payload = _run_graph_with_optional_resume(
            graph=graph,
            text=settings.sample_query,
            high_stakes=False,
            review_action=review_action,
            review_edits=review_edits,
        )
        result["final_payload"] = payload
        typer.echo(json.dumps(result, indent=2))
    finally:
        runtime.close()


@app.command("validate-tools")
def validate_tools(text: str = typer.Option("EGFR pathway evidence", "--text")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    runtime = build_runtime(settings)

    try:
        validations: dict[str, Any] = {
            "neo4j_connectivity": runtime.neo4j_service.verify_connectivity(),
            "tool_contracts": {},
        }

        resolved = runtime.neo4j_service.resolve_entities_by_text(text, top_k=1)
        entity_id = str(resolved[0]["candidate_id"]) if resolved else "EGFR"

        subgraph = runtime.neo4j_tools.get_subgraph_for_entity(SubgraphRequest(entity_id=entity_id))
        similar = runtime.neo4j_tools.get_similar_entities(SimilarEntitiesRequest(entity_id=entity_id))
        pathway = runtime.neo4j_tools.get_pathway_context(PathwayContextRequest(entity_id=entity_id))
        pub = runtime.semantic_tools.search_publications(PublicationSearchRequest(query_text=text, top_k=2))
        evi = runtime.semantic_tools.search_evidence(EvidenceSearchRequest(query_text=text, top_k=2))
        score = runtime.scoring_tools.get_model_score(ModelScoreRequest(candidate_id=entity_id))

        citation_ids = [hit.citation_handle for hit in evi.hits[:2] if hit.citation_handle]
        prov = runtime.evidence_tools.get_provenance_for_claim(
            ProvenanceRequest(claim_id=entity_id, citation_ids=[str(cid) for cid in citation_ids])
        )

        validations["tool_contracts"] = {
            "get_subgraph_for_entity": subgraph.execution_metadata.model_dump(),
            "get_similar_entities": similar.execution_metadata.model_dump(),
            "get_pathway_context": pathway.execution_metadata.model_dump(),
            "search_publications": pub.execution_metadata.model_dump(),
            "search_evidence": evi.execution_metadata.model_dump(),
            "get_model_score": score.execution_metadata.model_dump(),
            "get_provenance_for_claim": prov.execution_metadata.model_dump(),
        }
        validations["sample_counts"] = {
            "graph_paths": len(subgraph.graph_paths),
            "similar_candidates": len(similar.candidates),
            "pathway_paths": len(pathway.graph_paths),
            "publication_hits": len(pub.hits),
            "evidence_hits": len(evi.hits),
            "has_model_score": score.model_score is not None,
            "provenance_rows": len(prov.provenance),
        }

        typer.echo(json.dumps(validations, indent=2))
    finally:
        runtime.close()


@app.command("inspect-state")
def inspect_state(
    text: str = typer.Option(..., "--text"),
    high_stakes: bool = typer.Option(False, "--high-stakes"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    graph, runtime = build_graph(runtime=build_runtime(settings))
    thread_id = f"inspect-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = initialize_state(text, high_stakes=high_stakes)

    transitions: list[dict[str, Any]] = []

    try:
        for update in graph.stream(initial_state, config=config, stream_mode="updates"):
            transitions.append(_summarize_update(update))

        final_state = graph.get_state(config)
        snapshot = final_state.values if hasattr(final_state, "values") else {}
        result = {
            "thread_id": thread_id,
            "transitions": transitions,
            "final_payload": snapshot.get("final_payload") if isinstance(snapshot, dict) else None,
        }
        typer.echo(json.dumps(result, indent=2))
    finally:
        runtime.close()


def _run_graph_with_optional_resume(
    *,
    graph,
    text: str,
    high_stakes: bool,
    review_action: str | None,
    review_edits: str | None,
) -> dict[str, Any]:
    thread_id = f"orch-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = initialize_state(text, high_stakes=high_stakes)

    first = graph.invoke(initial_state, config=config)
    if _is_interrupt(first):
        if not review_action:
            return {
                "status": "review_required",
                "thread_id": thread_id,
                "interrupt": _serialize_interrupt(first.get("__interrupt__")),
                "resume_instructions": {
                    "review_action_options": ["continue", "reject", "edit"],
                    "example": "python -m orchestration.app.cli run query --text '...' --review-action continue",
                },
            }

        payload = {"action": review_action}
        if review_action == "edit" and review_edits:
            try:
                payload["edits"] = json.loads(review_edits)
            except json.JSONDecodeError:
                payload["edits"] = {"raw": review_edits}

        resumed = graph.invoke(Command(resume=payload), config=config)
        if _is_interrupt(resumed):
            return {
                "status": "review_required",
                "thread_id": thread_id,
                "interrupt": _serialize_interrupt(resumed.get("__interrupt__")),
            }
        return _extract_final_payload(resumed)

    return _extract_final_payload(first)


def _extract_final_payload(result: dict[str, Any]) -> dict[str, Any]:
    if isinstance(result, dict) and "final_payload" in result:
        return result["final_payload"]
    return {"status": "unknown", "raw": result}


def _is_interrupt(result: dict[str, Any] | Any) -> bool:
    return isinstance(result, dict) and "__interrupt__" in result


def _serialize_interrupt(value: Any) -> Any:
    if isinstance(value, (tuple, list)):
        return [str(item) for item in value]
    return str(value)


def _summarize_update(update: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(update, dict):
        return {"update": str(update)}

    summary: dict[str, Any] = {}
    for node_name, payload in update.items():
        if isinstance(payload, dict):
            summary[node_name] = sorted(payload.keys())
        else:
            summary[node_name] = str(payload)
    return summary


if __name__ == "__main__":
    app()
