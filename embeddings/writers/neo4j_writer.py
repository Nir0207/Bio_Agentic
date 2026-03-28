from __future__ import annotations

import logging

from neo4j import Driver

from embeddings.models import EmbeddingRecord
from embeddings.utils import chunked

logger = logging.getLogger(__name__)


class Neo4jEmbeddingWriter:
    def __init__(self, driver: Driver, database: str, write_batch_size: int) -> None:
        self.driver = driver
        self.database = database
        self.write_batch_size = max(1, write_batch_size)

    @staticmethod
    def build_payload(records: list[EmbeddingRecord]) -> list[dict]:
        return [
            {
                "id": record.node_id,
                "embedding": record.embedding,
                "embedding_model": record.embedding_model,
                "embedding_dim": record.embedding_dim,
                "embedding_created_at": record.embedding_created_at,
            }
            for record in records
        ]

    def write_embeddings(self, label: str, records: list[EmbeddingRecord]) -> int:
        if not records:
            return 0
        payload = self.build_payload(records)
        total_updated = 0
        query = f"""
        UNWIND $rows AS row
        MATCH (n:{label} {{id: row.id}})
        SET
          n.semantic_embedding = row.embedding,
          n.embedding_model = row.embedding_model,
          n.embedding_dim = row.embedding_dim,
          n.embedding_created_at = row.embedding_created_at
        RETURN count(n) AS updated
        """

        with self.driver.session(database=self.database) as session:
            for batch in chunked(payload, self.write_batch_size):
                result = session.run(query, {"rows": batch})
                updated = int(result.single()["updated"])
                if updated != len(batch):
                    raise ValueError(
                        f"Neo4j write mismatch for label {label}: updated {updated}, expected {len(batch)}"
                    )
                total_updated += updated

        logger.info("Wrote %s embeddings to label %s", total_updated, label)
        return total_updated
