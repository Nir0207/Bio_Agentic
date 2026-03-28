from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from orchestration.schemas.evidence_models import SemanticHit, ToolExecutionMetadata
from orchestration.services.semantic_service import SemanticService


class PublicationSearchRequest(BaseModel):
    query_text: str
    top_k: int = 5


class EvidenceSearchRequest(BaseModel):
    query_text: str
    top_k: int = 5


class SemanticSearchResult(BaseModel):
    hits: list[SemanticHit] = Field(default_factory=list)
    execution_metadata: ToolExecutionMetadata


class SemanticSearchTools:
    def __init__(self, service: SemanticService) -> None:
        self.service = service

    def search_publications(self, request: PublicationSearchRequest) -> SemanticSearchResult:
        started = datetime.now(timezone.utc).isoformat()
        hits, mode_used = self.service.search_publications(request.query_text, top_k=request.top_k)
        metadata = ToolExecutionMetadata(
            tool_name="search_publications",
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            status="ok",
            rows_read=len(hits),
            details={"query": request.query_text, "top_k": request.top_k, "mode_used": mode_used},
        )
        return SemanticSearchResult(hits=hits, execution_metadata=metadata)

    def search_evidence(self, request: EvidenceSearchRequest) -> SemanticSearchResult:
        started = datetime.now(timezone.utc).isoformat()
        hits, mode_used = self.service.search_evidence(request.query_text, top_k=request.top_k)
        metadata = ToolExecutionMetadata(
            tool_name="search_evidence",
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            status="ok",
            rows_read=len(hits),
            details={"query": request.query_text, "top_k": request.top_k, "mode_used": mode_used},
        )
        return SemanticSearchResult(hits=hits, execution_metadata=metadata)
