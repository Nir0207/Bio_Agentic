from __future__ import annotations

from typing import Any

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

GRAPH_LIST_QUERY = """
CALL gds.graph.list()
YIELD graphName, database, nodeCount, relationshipCount, schemaWithOrientation, creationTime
RETURN graphName, database, nodeCount, relationshipCount, schemaWithOrientation AS schema, creationTime
ORDER BY graphName
""".strip()

GRAPH_INSPECT_QUERY = """
CALL gds.graph.list($graphName)
YIELD graphName, database, nodeCount, relationshipCount, schemaWithOrientation, creationTime
RETURN graphName, database, nodeCount, relationshipCount, schemaWithOrientation AS schema, creationTime
""".strip()

GRAPH_PROJECT_NATIVE_QUERY = """
CALL gds.graph.project($graphName, $nodeProjection, $relationshipProjection)
YIELD graphName, nodeCount, relationshipCount, projectMillis
RETURN graphName, nodeCount, relationshipCount, projectMillis
""".strip()

GRAPH_PROJECT_CYPHER_QUERY = """
CALL gds.graph.project.cypher(
  $graphName,
  $nodeQuery,
  $relationshipQuery,
  $configuration
)
YIELD graphName, nodeCount, relationshipCount, projectMillis
RETURN graphName, nodeCount, relationshipCount, projectMillis
""".strip()


PROJECTION_ESTIMATE_NATIVE_QUERY = """
CALL gds.graph.project.estimate($nodeProjection, $relationshipProjection, $configuration)
YIELD requiredMemory, treeView, bytesMin, bytesMax, nodeCount, relationshipCount
RETURN requiredMemory, treeView, bytesMin, bytesMax, nodeCount, relationshipCount
""".strip()

PROJECTION_ESTIMATE_CYPHER_QUERY = """
CALL gds.graph.project.cypher.estimate($nodeQuery, $relationshipQuery, $configuration)
YIELD requiredMemory, treeView, bytesMin, bytesMax, nodeCount, relationshipCount
RETURN requiredMemory, treeView, bytesMin, bytesMax, nodeCount, relationshipCount
""".strip()


def build_native_projection_payload(
    graph_name: str,
    node_labels: list[str],
    relationship_types: list[str],
    node_properties: list[str] | None = None,
) -> dict[str, Any]:
    node_projection: dict[str, Any] = {}
    for label in node_labels:
        if node_properties:
            node_projection[label] = {"properties": node_properties}
        else:
            node_projection[label] = {}
    relationship_projection = {
        rel_type: {"type": rel_type, "orientation": "UNDIRECTED"}
        for rel_type in relationship_types
    }
    return {
        "graphName": graph_name,
        "nodeProjection": node_projection,
        "relationshipProjection": relationship_projection,
    }


def build_cypher_projection_payload(
    graph_name: str,
    node_labels: list[str],
    relationship_types: list[str],
) -> dict[str, Any]:
    label_list = _to_cypher_string_list(node_labels)
    rel_type_list = _to_cypher_string_list(relationship_types)

    node_query = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN [__LABEL_LIST__])
    RETURN id(n) AS id, labels(n) AS labels
    """.strip().replace("__LABEL_LIST__", label_list)

    relationship_query = """
    MATCH (source)-[r]->(target)
    WHERE type(r) IN [__REL_TYPE_LIST__]
      AND any(label IN labels(source) WHERE label IN [__LABEL_LIST__])
      AND any(label IN labels(target) WHERE label IN [__LABEL_LIST__])
    RETURN id(source) AS source, id(target) AS target, type(r) AS type
    """.strip().replace("__LABEL_LIST__", label_list).replace("__REL_TYPE_LIST__", rel_type_list)

    return {
        "graphName": graph_name,
        "nodeQuery": node_query,
        "relationshipQuery": relationship_query,
    }


def _to_cypher_string_list(values: list[str]) -> str:
    escaped = [value.replace("'", "\\'") for value in values]
    return ",".join(f"'{value}'" for value in escaped)
