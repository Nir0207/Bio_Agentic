from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import GraphEdge, GraphNode, GraphPath, ToolExecutionMetadata
from orchestration.services.neo4j_service import Neo4jService


class SubgraphRequest(BaseModel):
    entity_id: str
    max_hops: int = 2
    max_paths: int = 4


class SubgraphResult(BaseModel):
    graph_paths: list[GraphPath] = Field(default_factory=list)
    execution_metadata: ToolExecutionMetadata


class SimilarEntitiesRequest(BaseModel):
    entity_id: str
    top_k: int = 5


class SimilarEntitiesResult(BaseModel):
    candidates: list[CandidateEntity] = Field(default_factory=list)
    execution_metadata: ToolExecutionMetadata


class PathwayContextRequest(BaseModel):
    entity_id: str
    top_k: int = 5


class PathwayContextResult(BaseModel):
    graph_paths: list[GraphPath] = Field(default_factory=list)
    execution_metadata: ToolExecutionMetadata


class Neo4jTools:
    def __init__(self, service: Neo4jService) -> None:
        self.service = service

    def get_subgraph_for_entity(self, request: SubgraphRequest) -> SubgraphResult:
        started = datetime.now(timezone.utc).isoformat()
        rows = self.service.get_subgraph_for_entity(
            request.entity_id,
            max_hops=request.max_hops,
            max_paths=request.max_paths,
        )
        paths = [
            GraphPath(
                candidate_id=str(row.get("candidate_id") or request.entity_id),
                candidate_type=str(row.get("candidate_type") or "Unknown"),
                path_summary=str(row.get("path_summary") or ""),
                nodes=[GraphNode(**node) for node in row.get("nodes", [])],
                edges=[GraphEdge(**edge) for edge in row.get("edges", [])],
                relation_types=[str(item) for item in row.get("relation_types", [])],
                confidence=float(row.get("confidence") or 0.0),
                source_metadata=dict(row.get("source_metadata") or {}),
                supporting_source_systems=[str(item) for item in row.get("supporting_source_systems", [])],
            )
            for row in rows
        ]
        metadata = ToolExecutionMetadata(
            tool_name="get_subgraph_for_entity",
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            status="ok",
            rows_read=len(rows),
            details={"entity_id": request.entity_id, "max_hops": request.max_hops, "max_paths": request.max_paths},
        )
        return SubgraphResult(graph_paths=paths, execution_metadata=metadata)

    def get_similar_entities(self, request: SimilarEntitiesRequest) -> SimilarEntitiesResult:
        started = datetime.now(timezone.utc).isoformat()
        rows = self.service.get_similar_entities(request.entity_id, top_k=request.top_k)
        candidates = [
            CandidateEntity(
                candidate_id=str(row.get("candidate_id")),
                candidate_type=str(row.get("candidate_type") or "Protein"),
                display_name=str(row.get("display_name") or row.get("candidate_id")),
                sources=["graph_similarity"],
                graph_support=float(row.get("similarity") or 0.0),
            )
            for row in rows
        ]
        metadata = ToolExecutionMetadata(
            tool_name="get_similar_entities",
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            status="ok",
            rows_read=len(rows),
            details={"entity_id": request.entity_id, "top_k": request.top_k},
        )
        return SimilarEntitiesResult(candidates=candidates, execution_metadata=metadata)

    def get_pathway_context(self, request: PathwayContextRequest) -> PathwayContextResult:
        started = datetime.now(timezone.utc).isoformat()
        rows = self.service.get_pathway_context(request.entity_id, top_k=request.top_k)
        paths = [
            GraphPath(
                candidate_id=str(row.get("candidate_id") or request.entity_id),
                candidate_type=str(row.get("candidate_type") or "Unknown"),
                path_summary=str(row.get("path_summary") or ""),
                nodes=[GraphNode(**node) for node in row.get("nodes", [])],
                edges=[GraphEdge(**edge) for edge in row.get("edges", [])],
                relation_types=[str(item) for item in row.get("relation_types", [])],
                confidence=float(row.get("confidence") or 0.0),
                source_metadata=dict(row.get("source_metadata") or {}),
                supporting_source_systems=[str(item) for item in row.get("supporting_source_systems", [])],
            )
            for row in rows
        ]
        metadata = ToolExecutionMetadata(
            tool_name="get_pathway_context",
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            status="ok",
            rows_read=len(rows),
            details={"entity_id": request.entity_id, "top_k": request.top_k},
        )
        return PathwayContextResult(graph_paths=paths, execution_metadata=metadata)
