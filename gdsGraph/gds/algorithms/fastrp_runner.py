from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from gds.app.config import Settings
from gds.app.neo4j_client import Neo4jClient
from gds.writers.writeback import write_graph_embedding_metadata

logger = logging.getLogger(__name__)

FASTRP_MUTATE_QUERY = """
CALL gds.fastRP.mutate($graphName, $config)
YIELD nodePropertiesWritten, computeMillis, mutateMillis, preProcessingMillis
RETURN nodePropertiesWritten, computeMillis, mutateMillis, preProcessingMillis
""".strip()

NODE_PROPERTY_WRITE_QUERY = """
CALL gds.graph.nodeProperties.write($graphName, $nodeProperties, $nodeLabels, $configuration)
YIELD writeMillis, propertiesWritten
RETURN writeMillis, propertiesWritten
""".strip()


@dataclass(frozen=True)
class FastRPResult:
    node_properties_written: int
    metadata_rows_updated: int
    compute_millis: int
    write_millis: int
    pre_processing_millis: int


def build_fastrp_write_config(settings: Settings) -> dict[str, Any]:
    return {
        "embeddingDimension": settings.fastrp_embedding_dim,
        "iterationWeights": settings.fastrp_iteration_weights,
        "normalizationStrength": settings.fastrp_normalization_strength,
        "mutateProperty": "graph_embedding",
    }


def run_fastrp(client: Neo4jClient, settings: Settings) -> FastRPResult:
    config = build_fastrp_write_config(settings)
    mutate_row = client.single(
        FASTRP_MUTATE_QUERY,
        {
            "graphName": settings.gds_graph_name,
            "config": config,
        },
    )
    write_row = client.single(
        NODE_PROPERTY_WRITE_QUERY,
        {
            "graphName": settings.gds_graph_name,
            "nodeProperties": ["graph_embedding"],
            "nodeLabels": settings.gds_node_labels,
            "configuration": {},
        },
    )
    metadata_rows = write_graph_embedding_metadata(
        client=client,
        labels=settings.gds_node_labels,
        embedding_dim=settings.fastrp_embedding_dim,
    )
    result = FastRPResult(
        node_properties_written=int(mutate_row.get("nodePropertiesWritten", 0)),
        metadata_rows_updated=metadata_rows,
        compute_millis=int(mutate_row.get("computeMillis", 0)),
        write_millis=int(write_row.get("writeMillis", 0)),
        pre_processing_millis=int(mutate_row.get("preProcessingMillis", 0)),
    )
    logger.info(
        "FastRP complete: nodePropertiesWritten=%s metadataRows=%s computeMs=%s",
        result.node_properties_written,
        result.metadata_rows_updated,
        result.compute_millis,
    )
    return result
