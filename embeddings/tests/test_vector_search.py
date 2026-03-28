from __future__ import annotations

import pytest

from embeddings.models import SearchResult
from embeddings.retrieval.query_templates import build_vector_index_cypher
from embeddings.retrieval.vector_search import format_merged_search_response


def test_build_vector_index_cypher_is_idempotent_template() -> None:
    cypher = build_vector_index_cypher(
        index_name="publication_semantic_embedding_idx",
        label="Publication",
        property_name="semantic_embedding",
        dimensions=384,
        similarity_function="cosine",
    )
    assert "CREATE VECTOR INDEX publication_semantic_embedding_idx IF NOT EXISTS" in cypher
    assert "`vector.dimensions`: 384" in cypher
    assert "`vector.similarity_function`: 'cosine'" in cypher


def test_build_vector_index_cypher_rejects_invalid_identifier() -> None:
    with pytest.raises(ValueError, match="Invalid Neo4j identifier"):
        build_vector_index_cypher(
            index_name="bad-name",
            label="Publication",
            property_name="semantic_embedding",
            dimensions=384,
            similarity_function="cosine",
        )


def test_format_merged_search_response_orders_by_score() -> None:
    publication = [
        SearchResult(
            node_id="pub:1",
            label="Publication",
            score=0.44,
            snippet="Publication snippet",
            source_metadata={"source": "PubMed"},
        )
    ]
    evidence = [
        SearchResult(
            node_id="evi:1",
            label="Evidence",
            score=0.89,
            snippet="Evidence snippet",
            source_metadata={"source": "PubMed"},
        )
    ]
    merged = format_merged_search_response(publication, evidence, top_k=2)
    assert [row["node_id"] for row in merged] == ["evi:1", "pub:1"]
