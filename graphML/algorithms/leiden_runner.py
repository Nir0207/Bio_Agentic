from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from graphML.app.config import Settings
from graphML.app.neo4j_client import Neo4jClient
from graphML.writers.writeback import write_community_metadata

logger = logging.getLogger(__name__)

LEIDEN_WRITE_QUERY = """
CALL gds.leiden.write($graphName, $config)
YIELD communityCount, nodePropertiesWritten, ranLevels, computeMillis, writeMillis
RETURN communityCount, nodePropertiesWritten, ranLevels, computeMillis, writeMillis
""".strip()


@dataclass(frozen=True)
class LeidenResult:
    community_count: int
    node_properties_written: int
    metadata_rows_updated: int
    ran_levels: int
    compute_millis: int
    write_millis: int


def build_leiden_write_config(settings: Settings) -> dict[str, Any]:
    return {
        "writeProperty": "community_id",
        "maxLevels": settings.leiden_max_levels,
    }


def run_leiden(client: Neo4jClient, settings: Settings) -> LeidenResult:
    config = build_leiden_write_config(settings)
    row = client.single(
        LEIDEN_WRITE_QUERY,
        {
            "graphName": settings.gds_graph_name,
            "config": config,
        },
    )
    metadata_rows = write_community_metadata(client=client, labels=settings.gds_node_labels)
    result = LeidenResult(
        community_count=int(row.get("communityCount", 0)),
        node_properties_written=int(row.get("nodePropertiesWritten", 0)),
        metadata_rows_updated=metadata_rows,
        ran_levels=int(row.get("ranLevels", 0)),
        compute_millis=int(row.get("computeMillis", 0)),
        write_millis=int(row.get("writeMillis", 0)),
    )
    logger.info(
        "Leiden complete: communities=%s nodePropertiesWritten=%s metadataRows=%s",
        result.community_count,
        result.node_properties_written,
        result.metadata_rows_updated,
    )
    return result
