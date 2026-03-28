from __future__ import annotations

import logging
from pathlib import Path

from neo4j import GraphDatabase

from app.config import Settings

logger = logging.getLogger(__name__)


def run_validations(settings: Settings) -> dict[str, list[dict]]:
    query_file = Path(__file__).resolve().parent / "cypher" / "06_validation.cypher"
    queries = [block.strip() for block in query_file.read_text(encoding="utf-8").split("\n\n") if block.strip()]
    results: dict[str, list[dict]] = {}
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        with driver.session(database=settings.neo4j_database) as session:
            for index, query in enumerate(queries, start=1):
                result = session.run(query)
                records = [record.data() for record in result]
                results[f"query_{index}"] = records
                logger.info("Validation query %s returned %s rows", index, len(records))
    return results

