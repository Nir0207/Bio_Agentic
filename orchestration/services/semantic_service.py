from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from orchestration.schemas.evidence_models import SemanticHit
from orchestration.services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


@dataclass
class SemanticService:
    neo4j_service: Neo4jService
    retrieval_mode: str = "keyword"
    publication_index_name: str = "publication_semantic_embedding_idx"
    evidence_index_name: str = "evidence_semantic_embedding_idx"
    _embedding_model: Any | None = field(default=None, init=False, repr=False)

    def search_publications(self, query_text: str, top_k: int) -> tuple[list[SemanticHit], str]:
        rows, mode_used = self._search_rows(query_text, top_k, is_publication=True)
        hits = [
            SemanticHit(
                node_id=str(row.get("node_id")),
                node_type="Publication",
                retrieval_score=float(row.get("score") or 0.0),
                snippet=str(row.get("snippet") or ""),
                title=str(row.get("title") or "") or None,
                source_metadata={"source": row.get("source")},
                citation_handle=str(row.get("citation_handle") or row.get("node_id")),
                linked_candidate_ids=[],
            )
            for row in rows
        ]
        return hits, mode_used

    def search_evidence(self, query_text: str, top_k: int) -> tuple[list[SemanticHit], str]:
        rows, mode_used = self._search_rows(query_text, top_k, is_publication=False)
        hits = [
            SemanticHit(
                node_id=str(row.get("node_id")),
                node_type="Evidence",
                retrieval_score=float(row.get("score") or 0.0),
                snippet=str(row.get("snippet") or ""),
                title=None,
                source_metadata={"source": row.get("source")},
                citation_handle=str(row.get("citation_handle") or row.get("node_id")),
                linked_candidate_ids=[str(row.get("linked_candidate_id"))]
                if row.get("linked_candidate_id")
                else [],
            )
            for row in rows
        ]
        return hits, mode_used

    def _search_rows(self, query_text: str, top_k: int, *, is_publication: bool) -> tuple[list[dict[str, Any]], str]:
        strategy = self.retrieval_mode.lower()
        use_vector = strategy in {"vector", "hybrid"}

        if use_vector:
            try:
                embedding = self._embed_query(query_text)
                if is_publication:
                    rows = self.neo4j_service.search_publications_vector(
                        embedding,
                        index_name=self.publication_index_name,
                        top_k=top_k,
                    )
                else:
                    rows = self.neo4j_service.search_evidence_vector(
                        embedding,
                        index_name=self.evidence_index_name,
                        top_k=top_k,
                    )
                if rows:
                    return rows, "vector"
            except Exception as exc:
                logger.warning("Vector semantic retrieval failed; falling back to keyword mode: %s", exc)
                if strategy == "vector":
                    # Strict vector mode still returns fallback data to keep flow operable.
                    pass

        if is_publication:
            return self.neo4j_service.search_publications_keyword(query_text, top_k), "keyword"
        return self.neo4j_service.search_evidence_keyword(query_text, top_k), "keyword"

    def _embed_query(self, query_text: str) -> list[float]:
        cleaned = query_text.strip()
        if not cleaned:
            raise ValueError("Query text must be non-empty")

        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except Exception as exc:  # pragma: no cover - optional runtime dependency
                raise RuntimeError("sentence-transformers is required for vector retrieval mode") from exc
            self._embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        vectors = self._embedding_model.encode([cleaned], normalize_embeddings=True)
        if len(vectors) != 1:
            raise RuntimeError("Embedding model returned unexpected vector count")
        return [float(x) for x in vectors[0]]
