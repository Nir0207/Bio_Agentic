from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from gds.app.config import Settings
from gds.app.neo4j_client import Neo4jClient
from gds.projections.projection_queries import (
    PROJECTION_ESTIMATE_CYPHER_QUERY,
    PROJECTION_ESTIMATE_NATIVE_QUERY,
    build_cypher_projection_payload,
    build_native_projection_payload,
)

logger = logging.getLogger(__name__)

FASTRP_ESTIMATE_QUERY = """
CALL gds.fastRP.mutate.estimate($graphName, $config)
YIELD requiredMemory, treeView, bytesMin, bytesMax
RETURN requiredMemory, treeView, bytesMin, bytesMax
""".strip()

LEIDEN_ESTIMATE_QUERY = """
CALL gds.leiden.write.estimate($graphName, $config)
YIELD requiredMemory, treeView, bytesMin, bytesMax
RETURN requiredMemory, treeView, bytesMin, bytesMax
""".strip()

KNN_ESTIMATE_QUERY = """
CALL gds.knn.write.estimate($graphName, $config)
YIELD requiredMemory, treeView, bytesMin, bytesMax
RETURN requiredMemory, treeView, bytesMin, bytesMax
""".strip()


@dataclass(frozen=True)
class MemoryEstimateResult:
    name: str
    required_memory: str
    bytes_min: int | None
    bytes_max: int | None
    node_count: int | None
    relationship_count: int | None
    threshold_bytes: int
    within_threshold: bool
    insufficient_memory_warning: bool
    warnings: list[str]
    raw: dict[str, Any]

    @property
    def bytes_max_gb(self) -> float | None:
        if self.bytes_max is None:
            return None
        return self.bytes_max / (1024**3)


@dataclass(frozen=True)
class EstimateBundle:
    projection: MemoryEstimateResult
    fastrp: MemoryEstimateResult | None
    leiden: MemoryEstimateResult | None
    knn: MemoryEstimateResult | None


def build_fastrp_estimate_payload(settings: Settings) -> dict[str, Any]:
    return {
        "graphName": settings.gds_graph_name,
        "config": {
            "embeddingDimension": settings.fastrp_embedding_dim,
            "iterationWeights": settings.fastrp_iteration_weights,
            "normalizationStrength": settings.fastrp_normalization_strength,
            "mutateProperty": "graph_embedding",
        },
    }


def build_leiden_estimate_payload(settings: Settings) -> dict[str, Any]:
    return {
        "graphName": settings.gds_graph_name,
        "config": {
            "writeProperty": "community_id",
            "maxLevels": settings.leiden_max_levels,
        },
    }


def build_knn_estimate_payload(settings: Settings) -> dict[str, Any]:
    return {
        "graphName": settings.gds_graph_name,
        "config": {
            "nodeProperties": ["graph_embedding"],
            "nodeLabels": settings.knn_node_labels,
            "topK": settings.knn_top_k,
            "similarityCutoff": settings.knn_similarity_cutoff,
            "writeRelationshipType": settings.knn_rel_type,
            "writeProperty": "score",
        },
    }


def estimate_projection_memory(client: Neo4jClient, settings: Settings) -> MemoryEstimateResult:
    if settings.gds_projection_mode == "cypher":
        payload = build_cypher_projection_payload(
            graph_name=settings.gds_graph_name,
            node_labels=settings.gds_node_labels,
            relationship_types=settings.gds_relationship_types,
        )
        row = client.single(
            PROJECTION_ESTIMATE_CYPHER_QUERY,
            {
                "nodeQuery": payload["nodeQuery"],
                "relationshipQuery": payload["relationshipQuery"],
                "configuration": {},
            },
        )
    else:
        payload = build_native_projection_payload(
            graph_name=settings.gds_graph_name,
            node_labels=settings.gds_node_labels,
            relationship_types=settings.gds_relationship_types,
        )
        row = client.single(
            PROJECTION_ESTIMATE_NATIVE_QUERY,
            {
                "nodeProjection": payload["nodeProjection"],
                "relationshipProjection": payload["relationshipProjection"],
                "configuration": {},
            },
        )

    return _build_result(name="projection", row=row, threshold_bytes=settings.gds_max_memory_bytes)


def estimate_fastrp_memory(client: Neo4jClient, settings: Settings) -> MemoryEstimateResult:
    payload = build_fastrp_estimate_payload(settings)
    row = client.single(FASTRP_ESTIMATE_QUERY, payload)
    return _build_result(name="fastrp", row=row, threshold_bytes=settings.gds_max_memory_bytes)


def estimate_leiden_memory(client: Neo4jClient, settings: Settings) -> MemoryEstimateResult:
    payload = build_leiden_estimate_payload(settings)
    row = client.single(LEIDEN_ESTIMATE_QUERY, payload)
    return _build_result(name="leiden", row=row, threshold_bytes=settings.gds_max_memory_bytes)


def estimate_knn_memory(client: Neo4jClient, settings: Settings) -> MemoryEstimateResult:
    payload = build_knn_estimate_payload(settings)
    row = client.single(KNN_ESTIMATE_QUERY, payload)
    return _build_result(name="knn", row=row, threshold_bytes=settings.gds_max_memory_bytes)


def assert_estimate_safe(estimate: MemoryEstimateResult) -> None:
    if estimate.insufficient_memory_warning:
        raise RuntimeError(
            f"{estimate.name} memory estimate indicates insufficient Neo4j memory: {estimate.required_memory}"
        )
    if not estimate.within_threshold:
        threshold_gb = estimate.threshold_bytes / (1024**3)
        used_gb = estimate.bytes_max_gb
        raise RuntimeError(
            f"{estimate.name} memory estimate exceeds threshold {threshold_gb:.2f} GiB "
            f"(estimated max={used_gb:.2f} GiB)"
        )


def _build_result(name: str, row: dict[str, Any], threshold_bytes: int) -> MemoryEstimateResult:
    required_memory = str(row.get("requiredMemory", "unknown"))
    bytes_min = _to_optional_int(row.get("bytesMin"))
    bytes_max = _to_optional_int(row.get("bytesMax"))
    node_count = _to_optional_int(row.get("nodeCount"))
    relationship_count = _to_optional_int(row.get("relationshipCount"))

    inferred_bytes_max = bytes_max or _memory_text_to_bytes(required_memory)
    memory_text = f"{required_memory} {row.get('treeView', '')}".lower()

    warnings: list[str] = []
    insufficient_memory_warning = any(
        token in memory_text
        for token in (
            "insufficient",
            "not enough",
            "exceeds",
            "cannot allocate",
            "out of memory",
        )
    )
    if insufficient_memory_warning:
        warnings.append("Neo4j/GDS reported insufficient memory warning in estimate output")

    within_threshold = inferred_bytes_max is None or inferred_bytes_max <= threshold_bytes
    if not within_threshold:
        warnings.append(
            f"Estimated max memory {inferred_bytes_max / (1024**3):.2f} GiB exceeds configured threshold "
            f"{threshold_bytes / (1024**3):.2f} GiB"
        )

    result = MemoryEstimateResult(
        name=name,
        required_memory=required_memory,
        bytes_min=bytes_min,
        bytes_max=inferred_bytes_max,
        node_count=node_count,
        relationship_count=relationship_count,
        threshold_bytes=threshold_bytes,
        within_threshold=within_threshold,
        insufficient_memory_warning=insufficient_memory_warning,
        warnings=warnings,
        raw=row,
    )
    logger.info(
        "Estimate %s: requiredMemory=%s bytesMax=%s withinThreshold=%s",
        name,
        result.required_memory,
        result.bytes_max,
        result.within_threshold,
    )
    return result


def _memory_text_to_bytes(text: str) -> int | None:
    match = re.search(r"([0-9]*\.?[0-9]+)\s*(KiB|MiB|GiB|TiB|KB|MB|GB|TB|B)", text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    factor = {
        "B": 1,
        "KB": 1000,
        "MB": 1000**2,
        "GB": 1000**3,
        "TB": 1000**4,
        "KiB": 1024,
        "MiB": 1024**2,
        "GiB": 1024**3,
        "TiB": 1024**4,
    }[unit]
    return int(value * factor)


def _to_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
