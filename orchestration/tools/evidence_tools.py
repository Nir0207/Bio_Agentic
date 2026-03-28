from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from orchestration.schemas.evidence_models import ProvenanceRecord, ToolExecutionMetadata
from orchestration.services.neo4j_service import Neo4jService


class ProvenanceRequest(BaseModel):
    claim_id: str
    citation_ids: list[str] = Field(default_factory=list)


class ProvenanceResult(BaseModel):
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    execution_metadata: ToolExecutionMetadata


class EvidenceTools:
    def __init__(self, neo4j_service: Neo4jService) -> None:
        self.neo4j_service = neo4j_service

    def get_provenance_for_claim(self, request: ProvenanceRequest) -> ProvenanceResult:
        started = datetime.now(timezone.utc).isoformat()
        rows = self.neo4j_service.get_provenance_for_claim(request.claim_id, request.citation_ids)
        provenance = [ProvenanceRecord(**row) for row in rows]
        metadata = ToolExecutionMetadata(
            tool_name="get_provenance_for_claim",
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            status="ok",
            rows_read=len(provenance),
            details={"claim_id": request.claim_id, "citation_count": len(request.citation_ids)},
        )
        return ProvenanceResult(provenance=provenance, execution_metadata=metadata)
