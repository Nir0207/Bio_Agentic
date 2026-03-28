from __future__ import annotations

from orchestration.app.config import Settings
from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import GraphPath
from orchestration.tools.neo4j_tools import (
    Neo4jTools,
    PathwayContextRequest,
    SimilarEntitiesRequest,
    SubgraphRequest,
)


def retrieve_graph_node(state: OrchestrationState, *, neo4j_tools: Neo4jTools, settings: Settings) -> dict:
    normalized_query = str(state.get("normalized_query") or state.get("user_query") or "")
    target_entity_ids = list(state.get("target_entity_ids") or [])
    intent_type = str(state.get("intent_type") or "evidence_lookup")

    if not target_entity_ids:
        resolved = neo4j_tools.service.resolve_entities_by_text(normalized_query, top_k=settings.graph_top_k)
        target_entity_ids = [str(row.get("candidate_id")) for row in resolved if row.get("candidate_id")]

    graph_paths: list[GraphPath] = []
    candidates: dict[str, CandidateEntity] = {}

    metadata = dict(state.get("execution_metadata", {}))
    tool_runs = list(metadata.get("tool_runs", []))

    for entity_id in target_entity_ids[: settings.graph_top_k]:
        subgraph = neo4j_tools.get_subgraph_for_entity(
            SubgraphRequest(
                entity_id=entity_id,
                max_hops=settings.max_graph_hops,
                max_paths=settings.max_graph_paths,
            )
        )
        graph_paths.extend(subgraph.graph_paths)
        tool_runs.append(subgraph.execution_metadata.model_dump())

        for path in subgraph.graph_paths:
            candidate = candidates.get(path.candidate_id)
            if candidate is None:
                candidate = CandidateEntity(
                    candidate_id=path.candidate_id,
                    candidate_type=path.candidate_type,
                    display_name=path.nodes[0].display_name if path.nodes else path.candidate_id,
                    sources=["graph"],
                )
                candidates[path.candidate_id] = candidate
            candidate.graph_support = max(candidate.graph_support, float(path.confidence or 0.0))

        if intent_type == "similarity_lookup":
            similar = neo4j_tools.get_similar_entities(SimilarEntitiesRequest(entity_id=entity_id, top_k=settings.graph_top_k))
            tool_runs.append(similar.execution_metadata.model_dump())
            for candidate in similar.candidates:
                existing = candidates.get(candidate.candidate_id)
                if existing is None:
                    candidates[candidate.candidate_id] = candidate
                else:
                    existing.graph_support = max(existing.graph_support, candidate.graph_support)
                    if "graph_similarity" not in existing.sources:
                        existing.sources.append("graph_similarity")

        if intent_type == "pathway_exploration":
            pathway_ctx = neo4j_tools.get_pathway_context(PathwayContextRequest(entity_id=entity_id, top_k=settings.graph_top_k))
            graph_paths.extend(pathway_ctx.graph_paths)
            tool_runs.append(pathway_ctx.execution_metadata.model_dump())

    metadata["tool_runs"] = tool_runs
    metadata = add_stage_metadata(
        {**state, "execution_metadata": metadata},
        "retrieve_graph",
        {
            "target_entity_count": len(target_entity_ids),
            "graph_path_count": len(graph_paths),
            "candidate_count": len(candidates),
        },
    )

    return {
        "target_entity_ids": target_entity_ids,
        "graph_evidence": graph_paths,
        "candidate_entities": sorted(candidates.values(), key=lambda c: c.candidate_id),
        "execution_metadata": metadata,
    }
