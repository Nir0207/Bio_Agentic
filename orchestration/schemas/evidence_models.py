from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ToolExecutionMetadata(BaseModel):
    tool_name: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None
    status: str = "ok"
    rows_read: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    node_id: str
    node_labels: list[str] = Field(default_factory=list)
    display_name: str | None = None


class GraphEdge(BaseModel):
    edge_id: str
    relation_type: str
    source_node_id: str
    target_node_id: str
    confidence: float | None = None
    source_system: str | None = None


class GraphPath(BaseModel):
    candidate_id: str
    candidate_type: str
    path_summary: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    relation_types: list[str] = Field(default_factory=list)
    confidence: float | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    supporting_source_systems: list[str] = Field(default_factory=list)


class SemanticHit(BaseModel):
    node_id: str
    node_type: str
    retrieval_score: float
    snippet: str
    title: str | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    citation_handle: str | None = None
    linked_candidate_ids: list[str] = Field(default_factory=list)


class ModelScore(BaseModel):
    candidate_id: str
    score_name: str
    score_value: float
    model_name: str | None = None
    model_version: str | None = None
    run_id: str | None = None
    timestamp: str | None = None


class ProvenanceRecord(BaseModel):
    claim_id: str
    source_system: str
    source_ref: str
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfidenceSummary(BaseModel):
    overall_confidence: float
    graph_confidence: float
    semantic_confidence: float
    score_confidence: float
    reasons: list[str] = Field(default_factory=list)


class EvidenceBundle(BaseModel):
    candidate_id: str
    candidate_type: str
    graph_paths: list[GraphPath] = Field(default_factory=list)
    semantic_hits: list[SemanticHit] = Field(default_factory=list)
    model_scores: list[ModelScore] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    confidence_summary: ConfidenceSummary
    citation_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)
