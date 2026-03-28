from __future__ import annotations

import pytest

from embeddings.models import EmbeddingRecord
from embeddings.utils import validate_embedding_shapes
from embeddings.writers.neo4j_writer import Neo4jEmbeddingWriter


def test_validate_embedding_shapes_accepts_consistent_vectors() -> None:
    vectors = [[0.1, 0.2], [0.3, 0.4]]
    assert validate_embedding_shapes(vectors) == 2


def test_validate_embedding_shapes_rejects_mismatch() -> None:
    vectors = [[0.1, 0.2], [0.3]]
    with pytest.raises(ValueError, match="dimension mismatch"):
        validate_embedding_shapes(vectors)


def test_writer_payload_contains_embedding_metadata() -> None:
    record = EmbeddingRecord(
        node_id="publication:1",
        embedding=[0.1, 0.2, 0.3],
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dim=3,
        embedding_created_at="2026-03-28T00:00:00+00:00",
    )
    payload = Neo4jEmbeddingWriter.build_payload([record])
    assert payload == [
        {
            "id": "publication:1",
            "embedding": [0.1, 0.2, 0.3],
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dim": 3,
            "embedding_created_at": "2026-03-28T00:00:00+00:00",
        }
    ]
