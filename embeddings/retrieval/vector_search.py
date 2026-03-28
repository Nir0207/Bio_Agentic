from __future__ import annotations

import logging
from dataclasses import asdict

from neo4j import Driver

from embeddings.config import EmbeddingConfig
from embeddings.models import SearchResult
from embeddings.registry import TextEmbeddingModel
from embeddings.retrieval.query_templates import (
    EVIDENCE_VECTOR_SEARCH_QUERY,
    PUBLICATION_VECTOR_SEARCH_QUERY,
    build_vector_index_cypher,
)
from embeddings.utils import build_publication_text, normalize_text, truncate_snippet

logger = logging.getLogger(__name__)


class VectorSearchService:
    def __init__(
        self,
        *,
        driver: Driver,
        database: str,
        config: EmbeddingConfig,
        embedder: TextEmbeddingModel,
    ) -> None:
        self.driver = driver
        self.database = database
        self.config = config
        self.embedder = embedder

    def init_indexes(self) -> dict[str, int]:
        publication_dim = self._resolve_label_dimension("Publication")
        evidence_dim = self._resolve_label_dimension("Evidence")
        self._create_index(self.config.publication_index_name, "Publication", publication_dim)
        self._create_index(self.config.evidence_index_name, "Evidence", evidence_dim)
        return {"Publication": publication_dim, "Evidence": evidence_dim}

    def search_publication(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_embedding = self._embed_query(query)
        rows = self._run_vector_query(
            PUBLICATION_VECTOR_SEARCH_QUERY,
            index_name=self.config.publication_index_name,
            top_k=top_k,
            query_embedding=query_embedding,
        )
        results: list[SearchResult] = []
        for row in rows:
            snippet = truncate_snippet(build_publication_text(row.get("title"), row.get("abstract")))
            results.append(
                SearchResult(
                    node_id=row["node_id"],
                    label="Publication",
                    score=float(row["score"]),
                    snippet=snippet,
                    source_metadata={
                        "source": row.get("source"),
                        "pmid": row.get("pmid"),
                        "pub_year": row.get("pub_year"),
                    },
                )
            )
        return results

    def search_evidence(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_embedding = self._embed_query(query)
        rows = self._run_vector_query(
            EVIDENCE_VECTOR_SEARCH_QUERY,
            index_name=self.config.evidence_index_name,
            top_k=top_k,
            query_embedding=query_embedding,
        )
        results: list[SearchResult] = []
        for row in rows:
            snippet = truncate_snippet(normalize_text(row.get("text")))
            results.append(
                SearchResult(
                    node_id=row["node_id"],
                    label="Evidence",
                    score=float(row["score"]),
                    snippet=snippet,
                    source_metadata={
                        "source": row.get("source"),
                        "evidence_type": row.get("evidence_type"),
                        "confidence": row.get("confidence"),
                        "publication_id": row.get("publication_id"),
                    },
                )
            )
        return results

    def merged_search(self, query: str, top_k_each: int = 5) -> list[dict]:
        publication_results = self.search_publication(query=query, top_k=top_k_each)
        evidence_results = self.search_evidence(query=query, top_k=top_k_each)
        return format_merged_search_response(publication_results, evidence_results, top_k_each)

    def index_exists(self, index_name: str) -> bool:
        with self.driver.session(database=self.database) as session:
            rows = [
                record.data()
                for record in session.run(
                    """
                    SHOW VECTOR INDEXES
                    YIELD name
                    WHERE name = $index_name
                    RETURN name
                    """,
                    {"index_name": index_name},
                )
            ]
        return bool(rows)

    def _resolve_label_dimension(self, label: str) -> int:
        with self.driver.session(database=self.database) as session:
            record = session.run(
                f"""
                MATCH (n:{label})
                WHERE n.semantic_embedding IS NOT NULL
                WITH
                  count(n) AS node_count,
                  collect(DISTINCT size(n.semantic_embedding)) AS vector_sizes,
                  collect(DISTINCT toInteger(n.embedding_dim)) AS embedding_dim_values
                RETURN node_count, vector_sizes, embedding_dim_values
                """
            ).single()

        node_count = int(record["node_count"])
        if node_count == 0:
            raise ValueError(f"No {label} nodes with semantic embeddings found. Generate embeddings before index init.")
        vector_sizes = [int(size) for size in record["vector_sizes"] if size is not None]
        dim_values = [int(value) for value in record["embedding_dim_values"] if value is not None]
        dims = sorted(set(vector_sizes + dim_values))
        if len(dims) != 1:
            raise ValueError(f"Inconsistent embedding dimensions for {label}: {dims}")
        return dims[0]

    def _create_index(self, index_name: str, label: str, dimensions: int) -> None:
        query = build_vector_index_cypher(
            index_name=index_name,
            label=label,
            property_name="semantic_embedding",
            dimensions=dimensions,
            similarity_function=self.config.similarity_function,
        )
        with self.driver.session(database=self.database) as session:
            session.run(query).consume()
        logger.info(
            "Ensured vector index %s for %s.semantic_embedding (dim=%s, similarity=%s)",
            index_name,
            label,
            dimensions,
            self.config.similarity_function,
        )

    def _embed_query(self, query: str) -> list[float]:
        cleaned = normalize_text(query)
        if not cleaned:
            raise ValueError("Query cannot be empty")
        vectors = self.embedder.embed_texts([cleaned])
        if not vectors:
            raise ValueError("Embedding model returned no vectors for query")
        return vectors[0]

    def _run_vector_query(
        self,
        query: str,
        *,
        index_name: str,
        top_k: int,
        query_embedding: list[float],
    ) -> list[dict]:
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                {
                    "index_name": index_name,
                    "top_k": max(1, int(top_k)),
                    "query_embedding": query_embedding,
                },
            )
            return [record.data() for record in result]


def format_merged_search_response(
    publication_results: list[SearchResult],
    evidence_results: list[SearchResult],
    top_k: int,
) -> list[dict]:
    merged = publication_results + evidence_results
    merged.sort(key=lambda item: item.score, reverse=True)
    return [asdict(result) for result in merged[: max(1, top_k)]]
