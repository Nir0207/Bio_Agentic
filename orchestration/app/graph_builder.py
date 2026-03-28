from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from orchestration.app.config import Settings, get_settings
from orchestration.app.state import OrchestrationState
from orchestration.nodes.assemble_candidates import assemble_candidates_node
from orchestration.nodes.build_evidence_bundle import build_evidence_bundle_node
from orchestration.nodes.fetch_scores import fetch_scores_node
from orchestration.nodes.finalize_payload import finalize_payload_node
from orchestration.nodes.request_human_review import request_human_review_node
from orchestration.nodes.retrieve_graph import retrieve_graph_node
from orchestration.nodes.retrieve_semantic import retrieve_semantic_node
from orchestration.nodes.route_query import route_query_node
from orchestration.services.evidence_service import EvidenceService
from orchestration.services.neo4j_service import Neo4jService
from orchestration.services.scoring_service import ScoringService
from orchestration.services.semantic_service import SemanticService
from orchestration.tools.evidence_tools import EvidenceTools
from orchestration.tools.neo4j_tools import Neo4jTools
from orchestration.tools.scoring_tools import ScoringTools
from orchestration.tools.semantic_search_tools import SemanticSearchTools


@dataclass
class OrchestrationRuntime:
    settings: Settings
    neo4j_service: Neo4jService
    semantic_service: SemanticService
    scoring_service: ScoringService
    evidence_service: EvidenceService
    neo4j_tools: Neo4jTools
    semantic_tools: SemanticSearchTools
    scoring_tools: ScoringTools
    evidence_tools: EvidenceTools

    def close(self) -> None:
        self.neo4j_service.close()


@dataclass
class DependencyReport:
    neo4j_connectivity: dict[str, Any]
    upstream_directories: dict[str, bool]
    modeling_artifacts_root: str


def build_runtime(settings: Settings | None = None) -> OrchestrationRuntime:
    settings = settings or get_settings()

    neo4j_service = Neo4jService(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
        allow_mock_fallback_data=settings.allow_mock_fallback_data,
    )
    semantic_service = SemanticService(
        neo4j_service=neo4j_service,
        retrieval_mode=settings.semantic_retrieval_mode,
        publication_index_name=settings.vector_index_name_publication,
        evidence_index_name=settings.vector_index_name_evidence,
    )
    scoring_service = ScoringService(
        neo4j_service=neo4j_service,
        score_source=settings.model_score_source,
        score_name=settings.model_score_name,
        artifacts_root=settings.modeling_artifacts_root,
        allow_mock_fallback_data=settings.allow_mock_fallback_data,
    )
    evidence_service = EvidenceService()

    neo4j_tools = Neo4jTools(neo4j_service)
    semantic_tools = SemanticSearchTools(semantic_service)
    scoring_tools = ScoringTools(scoring_service)
    evidence_tools = EvidenceTools(neo4j_service)

    return OrchestrationRuntime(
        settings=settings,
        neo4j_service=neo4j_service,
        semantic_service=semantic_service,
        scoring_service=scoring_service,
        evidence_service=evidence_service,
        neo4j_tools=neo4j_tools,
        semantic_tools=semantic_tools,
        scoring_tools=scoring_tools,
        evidence_tools=evidence_tools,
    )


def verify_upstream_dependencies(runtime: OrchestrationRuntime) -> DependencyReport:
    settings = runtime.settings
    root = settings.project_root

    dirs = {
        "embeddings": (root / "embeddings").exists(),
        "graphML": (root / "graphML").exists(),
        "modeling": (root / "modeling").exists(),
    }

    connectivity = runtime.neo4j_service.verify_connectivity()

    return DependencyReport(
        neo4j_connectivity=connectivity,
        upstream_directories=dirs,
        modeling_artifacts_root=str(settings.modeling_artifacts_root),
    )


def build_graph(
    *,
    runtime: OrchestrationRuntime | None = None,
    checkpointer: Any | None = None,
):
    runtime = runtime or build_runtime()
    settings = runtime.settings

    builder = StateGraph(OrchestrationState)
    builder.add_node("route_query", route_query_node)
    builder.add_node(
        "retrieve_graph",
        lambda state: retrieve_graph_node(state, neo4j_tools=runtime.neo4j_tools, settings=settings),
    )
    builder.add_node(
        "retrieve_semantic",
        lambda state: retrieve_semantic_node(state, semantic_tools=runtime.semantic_tools, settings=settings),
    )
    builder.add_node(
        "fetch_scores",
        lambda state: fetch_scores_node(state, scoring_tools=runtime.scoring_tools),
    )
    builder.add_node(
        "assemble_candidates",
        lambda state: assemble_candidates_node(state, evidence_service=runtime.evidence_service),
    )
    builder.add_node(
        "build_evidence_bundle",
        lambda state: build_evidence_bundle_node(
            state,
            settings=settings,
            evidence_service=runtime.evidence_service,
            evidence_tools=runtime.evidence_tools,
        ),
    )
    builder.add_node(
        "request_human_review",
        lambda state: request_human_review_node(state, settings=settings, evidence_service=runtime.evidence_service),
    )
    builder.add_node("finalize_payload", finalize_payload_node)

    builder.add_edge(START, "route_query")
    builder.add_edge("route_query", "retrieve_graph")
    builder.add_edge("retrieve_graph", "retrieve_semantic")
    builder.add_edge("retrieve_semantic", "fetch_scores")
    builder.add_edge("fetch_scores", "assemble_candidates")
    builder.add_edge("assemble_candidates", "build_evidence_bundle")
    builder.add_edge("build_evidence_bundle", "request_human_review")
    builder.add_edge("request_human_review", "finalize_payload")
    builder.add_edge("finalize_payload", END)

    compiled = builder.compile(checkpointer=checkpointer or MemorySaver())
    return compiled, runtime
