from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from graphML.app.config import Settings
from graphML.app.neo4j_client import Neo4jClient
from graphML.projections.projection_queries import build_native_projection_payload
from graphML.writers.writeback import write_knn_relationship_metadata

logger = logging.getLogger(__name__)

KNN_WRITE_QUERY = """
CALL gds.knn.write($graphName, $config)
YIELD nodesCompared, relationshipsWritten, computeMillis, writeMillis
RETURN nodesCompared, relationshipsWritten, computeMillis, writeMillis
""".strip()

GRAPH_EXISTS_QUERY = """
CALL gds.graph.exists($graphName)
YIELD exists
RETURN exists
""".strip()

GRAPH_DROP_QUERY = """
CALL gds.graph.drop($graphName, false)
YIELD graphName
RETURN graphName
""".strip()

GRAPH_PROJECT_NATIVE_QUERY = """
CALL gds.graph.project($graphName, $nodeProjection, $relationshipProjection)
YIELD graphName
RETURN graphName
""".strip()


@dataclass(frozen=True)
class KNNResult:
    enabled: bool
    nodes_compared: int
    relationships_written: int
    metadata_rows_updated: int
    compute_millis: int
    write_millis: int


def build_knn_write_config(settings: Settings) -> dict[str, Any]:
    return {
        "nodeProperties": ["graph_embedding"],
        "nodeLabels": settings.knn_node_labels,
        "topK": settings.knn_top_k,
        "similarityCutoff": settings.knn_similarity_cutoff,
        "writeRelationshipType": settings.knn_rel_type,
        "writeProperty": "score",
    }


def run_knn(client: Neo4jClient, settings: Settings) -> KNNResult:
    if not settings.knn_enabled:
        return KNNResult(
            enabled=False,
            nodes_compared=0,
            relationships_written=0,
            metadata_rows_updated=0,
            compute_millis=0,
            write_millis=0,
        )

    _assert_graph_embeddings_present(client=client, labels=settings.knn_node_labels)
    _ensure_embedding_property_loaded_in_graph(client=client, settings=settings)
    config = build_knn_write_config(settings)
    row = client.single(
        KNN_WRITE_QUERY,
        {
            "graphName": settings.gds_graph_name,
            "config": config,
        },
    )
    metadata_rows = write_knn_relationship_metadata(client=client, rel_type=settings.knn_rel_type)
    result = KNNResult(
        enabled=True,
        nodes_compared=int(row.get("nodesCompared", 0)),
        relationships_written=int(row.get("relationshipsWritten", 0)),
        metadata_rows_updated=metadata_rows,
        compute_millis=int(row.get("computeMillis", 0)),
        write_millis=int(row.get("writeMillis", 0)),
    )
    logger.info(
        "KNN complete: nodesCompared=%s relationshipsWritten=%s metadataRows=%s",
        result.nodes_compared,
        result.relationships_written,
        result.metadata_rows_updated,
    )
    return result


def _assert_graph_embeddings_present(client: Neo4jClient, labels: list[str]) -> None:
    query = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN $labels)
      AND n.graph_embedding IS NOT NULL
    RETURN count(n) AS embedded
    """.strip()
    row = client.single(query, {"labels": labels})
    embedded = int(row.get("embedded", 0))
    if embedded <= 0:
        raise RuntimeError(
            "KNN requires graph_embedding on projected nodes. "
            "Run FastRP first and verify writeback before running KNN."
        )


def _ensure_embedding_property_loaded_in_graph(client: Neo4jClient, settings: Settings) -> None:
    query = """
    CALL gds.graph.nodeProperty.stream($graphName, $property, $labels)
    YIELD nodeId, propertyValue
    RETURN count(nodeId) AS streamed
    """.strip()
    try:
        client.single(
            query,
            {
                "graphName": settings.gds_graph_name,
                "property": "graph_embedding",
                "labels": settings.knn_node_labels,
            },
        )
    except Exception as exc:  # noqa: BLE001
        if "has not been loaded" not in str(exc):
            raise
        logger.info(
            "graph_embedding not loaded in graph '%s'; recreating projection with node property",
            settings.gds_graph_name,
        )
        _recreate_projection_with_embeddings(client=client, settings=settings)


def _recreate_projection_with_embeddings(client: Neo4jClient, settings: Settings) -> None:
    exists = client.single(GRAPH_EXISTS_QUERY, {"graphName": settings.gds_graph_name}).get("exists", False)
    if exists:
        client.single(GRAPH_DROP_QUERY, {"graphName": settings.gds_graph_name})

    payload = build_native_projection_payload(
        graph_name=settings.gds_graph_name,
        node_labels=settings.gds_node_labels,
        relationship_types=settings.gds_relationship_types,
        node_properties=["graph_embedding"],
    )
    client.single(
        GRAPH_PROJECT_NATIVE_QUERY,
        {
            "graphName": payload["graphName"],
            "nodeProjection": payload["nodeProjection"],
            "relationshipProjection": payload["relationshipProjection"],
        },
    )
