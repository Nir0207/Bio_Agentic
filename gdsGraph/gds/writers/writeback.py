from __future__ import annotations

from datetime import datetime, timezone

from gds.app.constants import FASTRP_MODEL_NAME, KNN_SOURCE_VALUE, LEIDEN_ALGORITHM_NAME
from gds.app.neo4j_client import Neo4jClient


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_graph_embedding_metadata(
    client: Neo4jClient,
    labels: list[str],
    embedding_dim: int,
    created_at: str | None = None,
) -> int:
    ts = created_at or utc_now_iso()
    query = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN $labels)
      AND n.graph_embedding IS NOT NULL
    SET n.graph_embedding_model = $model,
        n.graph_embedding_dim = $embeddingDim,
        n.graph_embedding_created_at = $createdAt
    RETURN count(n) AS updated
    """.strip()
    row = client.single(
        query,
        {
            "labels": labels,
            "embeddingDim": embedding_dim,
            "model": FASTRP_MODEL_NAME,
            "createdAt": ts,
        },
    )
    return int(row.get("updated", 0))


def write_community_metadata(client: Neo4jClient, labels: list[str], created_at: str | None = None) -> int:
    ts = created_at or utc_now_iso()
    query = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN $labels)
      AND n.community_id IS NOT NULL
    SET n.community_algorithm = $algorithm,
        n.community_created_at = $createdAt
    RETURN count(n) AS updated
    """.strip()
    row = client.single(
        query,
        {
            "labels": labels,
            "algorithm": LEIDEN_ALGORITHM_NAME,
            "createdAt": ts,
        },
    )
    return int(row.get("updated", 0))


def write_knn_relationship_metadata(client: Neo4jClient, rel_type: str, created_at: str | None = None) -> int:
    ts = created_at or utc_now_iso()
    query = """
    MATCH ()-[r]->()
    WHERE type(r) = $relType AND r.score IS NOT NULL
    SET r.source = $source,
        r.embedding_model = $model,
        r.created_at = $createdAt
    RETURN count(r) AS updated
    """.strip()
    row = client.single(
        query,
        {
            "relType": rel_type,
            "source": KNN_SOURCE_VALUE,
            "model": FASTRP_MODEL_NAME,
            "createdAt": ts,
        },
    )
    return int(row.get("updated", 0))
