from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class CandidateEntity(BaseModel):
    candidate_id: str
    candidate_type: str | None = None
    display_name: str | None = None
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    node_id: str
    node_labels: list[str] = Field(default_factory=list)
    display_name: str | None = None


class GraphEdge(BaseModel):
    edge_id: str | None = None
    relation_type: str
    source_node_id: str
    target_node_id: str
    confidence: float | None = None
    source_system: str | None = None


class GraphPath(BaseModel):
    path_id: str | None = None
    candidate_id: str | None = None
    candidate_type: str | None = None
    path_summary: str | None = None
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    relation_types: list[str] = Field(default_factory=list)
    confidence: float | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    supporting_source_systems: list[str] = Field(default_factory=list)


class SemanticEvidence(BaseModel):
    evidence_id: str
    node_type: str | None = None
    retrieval_score: float | None = None
    snippet: str = ""
    title: str | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    citation_id: str | None = None
    linked_candidate_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        data = dict(values)
        if "evidence_id" not in data:
            data["evidence_id"] = data.get("node_id")

        if "citation_id" not in data:
            data["citation_id"] = data.get("citation_handle")

        if "linked_candidate_ids" not in data and data.get("linked_candidate_id"):
            data["linked_candidate_ids"] = [str(data["linked_candidate_id"])]

        if "retrieval_score" not in data:
            data["retrieval_score"] = data.get("score")

        return data


class ModelScoreRecord(BaseModel):
    candidate_id: str
    score_name: str
    score_value: float
    model_name: str | None = None
    model_version: str | None = None
    run_id: str | None = None
    timestamp: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProvenanceRecord(BaseModel):
    claim_id: str | None = None
    source_system: str | None = None
    source_ref: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundleItem(BaseModel):
    candidate_id: str | None = None
    candidate_type: str | None = None
    summary: str | None = None
    graph_paths: list[GraphPath] = Field(default_factory=list)
    semantic_hits: list[SemanticEvidence] = Field(default_factory=list)
    model_scores: list[ModelScoreRecord] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerificationInputPayload(BaseModel):
    original_query: str = ""
    normalized_query: str = ""
    candidate_entities: list[CandidateEntity] = Field(default_factory=list)
    graph_evidence: list[GraphPath] = Field(default_factory=list)
    semantic_evidence: list[SemanticEvidence] = Field(default_factory=list)
    model_scores: list[ModelScoreRecord] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    evidence_bundle: list[EvidenceBundleItem] = Field(default_factory=list)
    draft_answer_text: str | None = None
    high_stakes: bool = False
    query_metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "extra": "allow",
    }

    @model_validator(mode="before")
    @classmethod
    def _normalize_aliases(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        data = dict(values)
        if not data.get("original_query"):
            data["original_query"] = data.get("user_query") or data.get("normalized_query") or ""

        if data.get("draft_answer_text") is None:
            data["draft_answer_text"] = data.get("draft_answer")

        if data.get("high_stakes") is None:
            metadata = data.get("query_metadata") if isinstance(data.get("query_metadata"), dict) else {}
            data["high_stakes"] = bool(metadata.get("high_stakes", False))

        return data
