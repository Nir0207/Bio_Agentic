from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from neo4j import Driver

from embeddings.config import EmbeddingConfig
from embeddings.models import EmbeddingInput, EmbeddingRecord, GenerationStats
from embeddings.registry import TextEmbeddingModel
from embeddings.utils import chunked, utc_timestamp, validate_embedding_shapes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratorQueries:
    count_total: str
    count_already_embedded: str
    fetch_candidates: str


class BaseEmbeddingGenerator:
    def __init__(
        self,
        driver: Driver,
        database: str,
        config: EmbeddingConfig,
        embedder: TextEmbeddingModel,
        label: str,
        queries: GeneratorQueries,
        text_builder: Callable[[dict], str],
    ) -> None:
        self.driver = driver
        self.database = database
        self.config = config
        self.embedder = embedder
        self.label = label
        self.queries = queries
        self.text_builder = text_builder

    def generate(self, *, force: bool | None = None, max_nodes: int | None = None) -> tuple[list[EmbeddingRecord], GenerationStats]:
        effective_force = self.config.force_reembed if force is None else force
        effective_max_nodes = self.config.max_nodes if max_nodes is None else max_nodes

        with self.driver.session(database=self.database) as session:
            total_nodes = int(session.run(self.queries.count_total).single()["count"])
            already_embedded = 0
            if not effective_force:
                already_embedded = int(session.run(self.queries.count_already_embedded).single()["count"])
            result = session.run(
                self.queries.fetch_candidates,
                {
                    "force": effective_force,
                    "max_nodes": int(effective_max_nodes),
                },
            )
            rows = [record.data() for record in result]

        prepared_inputs: list[EmbeddingInput] = []
        empty_text_skipped = 0

        for row in rows:
            text = self.text_builder(row)
            if not text:
                empty_text_skipped += 1
                continue
            prepared_inputs.append(
                EmbeddingInput(
                    node_id=row["id"],
                    text=text,
                    source_metadata={k: v for k, v in row.items() if k != "id"},
                )
            )

        records: list[EmbeddingRecord] = []
        failed = 0
        expected_dim = self.embedder.embedding_dim
        created_at = utc_timestamp()

        for batch in chunked(prepared_inputs, self.config.batch_size):
            texts = [item.text for item in batch]
            try:
                vectors = self.embedder.embed_texts(texts)
                batch_dim = validate_embedding_shapes(vectors, expected_dim)
                if expected_dim is None:
                    expected_dim = batch_dim
                elif batch_dim != expected_dim:
                    raise ValueError(
                        f"Embedding dimension mismatch for label {self.label}: got {batch_dim}, expected {expected_dim}"
                    )
                for item, vector in zip(batch, vectors, strict=True):
                    records.append(
                        EmbeddingRecord(
                            node_id=item.node_id,
                            embedding=vector,
                            embedding_model=self.embedder.model_name,
                            embedding_dim=expected_dim,
                            embedding_created_at=created_at,
                        )
                    )
            except ValueError:
                # Dimensional shape issues should fail the run immediately.
                raise
            except Exception as exc:  # noqa: BLE001
                failed += len(batch)
                logger.exception("Embedding batch failed for label %s: %s", self.label, exc)

        processed = len(records)
        skipped = already_embedded + empty_text_skipped

        stats = GenerationStats(
            label=self.label,
            total_nodes=total_nodes,
            already_embedded=already_embedded,
            candidates=len(rows),
            processed=processed,
            skipped=skipped,
            failed=failed,
            empty_text_skipped=empty_text_skipped,
        )

        logger.info(
            "Embedding generation complete for %s: total=%s candidates=%s processed=%s skipped=%s failed=%s",
            self.label,
            total_nodes,
            len(rows),
            processed,
            skipped,
            failed,
        )
        return records, stats
