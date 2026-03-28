from __future__ import annotations

from orchestration.app.config import Settings
from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.schemas.evidence_models import SemanticHit
from orchestration.tools.semantic_search_tools import EvidenceSearchRequest, PublicationSearchRequest, SemanticSearchTools


def retrieve_semantic_node(state: OrchestrationState, *, semantic_tools: SemanticSearchTools, settings: Settings) -> dict:
    normalized_query = str(state.get("normalized_query") or state.get("user_query") or "")
    target_entity_ids = [str(item).upper() for item in (state.get("target_entity_ids") or [])]

    publication_result = semantic_tools.search_publications(
        PublicationSearchRequest(query_text=normalized_query, top_k=settings.semantic_top_k)
    )
    evidence_result = semantic_tools.search_evidence(EvidenceSearchRequest(query_text=normalized_query, top_k=settings.semantic_top_k))

    hits: list[SemanticHit] = [*publication_result.hits, *evidence_result.hits]

    # Lightweight deterministic linking from textual mentions when explicit links are absent.
    for hit in hits:
        if hit.linked_candidate_ids:
            continue
        combined = f"{hit.title or ''} {hit.snippet}".upper()
        linked = [entity_id for entity_id in target_entity_ids if entity_id in combined]
        if linked:
            hit.linked_candidate_ids = linked

    hits.sort(key=lambda item: (-item.retrieval_score, item.node_id))

    metadata = dict(state.get("execution_metadata", {}))
    tool_runs = list(metadata.get("tool_runs", []))
    tool_runs.append(publication_result.execution_metadata.model_dump())
    tool_runs.append(evidence_result.execution_metadata.model_dump())
    metadata["tool_runs"] = tool_runs
    metadata = add_stage_metadata(
        {**state, "execution_metadata": metadata},
        "retrieve_semantic",
        {
            "semantic_hit_count": len(hits),
            "publication_hits": len(publication_result.hits),
            "evidence_hits": len(evidence_result.hits),
        },
    )

    return {
        "semantic_evidence": hits,
        "execution_metadata": metadata,
    }
