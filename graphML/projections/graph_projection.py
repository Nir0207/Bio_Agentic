from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from graphML.app.config import Settings
from graphML.app.neo4j_client import Neo4jClient
from graphML.projections.projection_queries import (
    GRAPH_DROP_QUERY,
    GRAPH_EXISTS_QUERY,
    GRAPH_INSPECT_QUERY,
    GRAPH_LIST_QUERY,
    GRAPH_PROJECT_CYPHER_QUERY,
    GRAPH_PROJECT_NATIVE_QUERY,
    build_cypher_projection_payload,
    build_native_projection_payload,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GraphCatalogEntry:
    graph_name: str
    database: str | None
    node_count: int
    relationship_count: int
    schema: Any | None
    creation_time: str | None


@dataclass(frozen=True)
class ProjectionCreateResult:
    graph_name: str
    created: bool
    reused: bool
    mode: str
    node_count: int
    relationship_count: int
    message: str


def graph_exists(client: Neo4jClient, graph_name: str) -> bool:
    record = client.single(GRAPH_EXISTS_QUERY, {"graphName": graph_name})
    return bool(record.get("exists", False))


def drop_graph(client: Neo4jClient, graph_name: str) -> bool:
    if not graph_exists(client, graph_name):
        return False
    client.single(GRAPH_DROP_QUERY, {"graphName": graph_name})
    logger.info("Dropped existing GDS graph '%s'", graph_name)
    return True


def list_graph_catalog(client: Neo4jClient) -> list[GraphCatalogEntry]:
    rows = client.run(GRAPH_LIST_QUERY)
    return [_to_entry(row) for row in rows]


def inspect_graph(client: Neo4jClient, graph_name: str) -> GraphCatalogEntry | None:
    row = client.single(GRAPH_INSPECT_QUERY, {"graphName": graph_name})
    if not row:
        return None
    return _to_entry(row)


def is_projection_compatible(entry: GraphCatalogEntry, settings: Settings) -> bool:
    schema_str = str(entry.schema or "")
    has_all_labels = all(label in schema_str for label in settings.gds_node_labels)
    has_all_relationships = all(rel_type in schema_str for rel_type in settings.gds_relationship_types)
    return has_all_labels and has_all_relationships


def create_or_reuse_projection(
    client: Neo4jClient,
    settings: Settings,
    replace: bool | None = None,
) -> ProjectionCreateResult:
    should_replace = settings.gds_replace_graph if replace is None else replace
    graph_name = settings.gds_graph_name

    if graph_exists(client, graph_name):
        if should_replace:
            drop_graph(client, graph_name)
        else:
            existing = inspect_graph(client, graph_name)
            if existing is None:
                raise RuntimeError(f"GDS graph '{graph_name}' exists but cannot be inspected")
            if not is_projection_compatible(existing, settings):
                raise RuntimeError(
                    f"GDS graph '{graph_name}' exists but is incompatible with configured labels/relationships. "
                    "Re-run with --replace or set GDS_REPLACE_GRAPH=true."
                )
            return ProjectionCreateResult(
                graph_name=graph_name,
                created=False,
                reused=True,
                mode="existing",
                node_count=existing.node_count,
                relationship_count=existing.relationship_count,
                message="Reused compatible in-memory GDS graph",
            )

    mode_order = [settings.gds_projection_mode]
    if settings.gds_projection_mode == "auto":
        mode_order = ["native", "cypher"]

    last_error: Exception | None = None
    for mode in mode_order:
        try:
            if mode == "native":
                payload = build_native_projection_payload(
                    graph_name=graph_name,
                    node_labels=settings.gds_node_labels,
                    relationship_types=settings.gds_relationship_types,
                )
                row = client.single(
                    GRAPH_PROJECT_NATIVE_QUERY,
                    {
                        "graphName": payload["graphName"],
                        "nodeProjection": payload["nodeProjection"],
                        "relationshipProjection": payload["relationshipProjection"],
                    },
                )
            elif mode == "cypher":
                payload = build_cypher_projection_payload(
                    graph_name=graph_name,
                    node_labels=settings.gds_node_labels,
                    relationship_types=settings.gds_relationship_types,
                )
                row = client.single(
                    GRAPH_PROJECT_CYPHER_QUERY,
                    {
                        "graphName": payload["graphName"],
                        "nodeQuery": payload["nodeQuery"],
                        "relationshipQuery": payload["relationshipQuery"],
                        "configuration": {},
                    },
                )
            else:
                raise RuntimeError(f"Unsupported projection mode: {mode}")

            return ProjectionCreateResult(
                graph_name=row.get("graphName", graph_name),
                created=True,
                reused=False,
                mode=mode,
                node_count=int(row.get("nodeCount", 0)),
                relationship_count=int(row.get("relationshipCount", 0)),
                message="Created new in-memory GDS graph projection",
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning("Projection creation failed in %s mode: %s", mode, exc)

    raise RuntimeError(f"Failed to create projection for '{graph_name}': {last_error}")


def _to_entry(row: dict[str, Any]) -> GraphCatalogEntry:
    return GraphCatalogEntry(
        graph_name=str(row.get("graphName", "")),
        database=row.get("database"),
        node_count=int(row.get("nodeCount", 0)),
        relationship_count=int(row.get("relationshipCount", 0)),
        schema=row.get("schema"),
        creation_time=row.get("creationTime"),
    )
