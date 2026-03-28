from __future__ import annotations

from neo4j import Driver

from embeddings.config import EmbeddingConfig
from embeddings.generators.base_generator import BaseEmbeddingGenerator, GeneratorQueries
from embeddings.registry import TextEmbeddingModel
from embeddings.utils import build_evidence_text


EVIDENCE_QUERIES = GeneratorQueries(
    count_total="""
    MATCH (n:Evidence)
    RETURN count(n) AS count
    """,
    count_already_embedded="""
    MATCH (n:Evidence)
    WHERE n.semantic_embedding IS NOT NULL
    RETURN count(n) AS count
    """,
    fetch_candidates="""
    MATCH (n:Evidence)
    WHERE $force OR n.semantic_embedding IS NULL
    WITH n
    ORDER BY n.id ASC
    LIMIT CASE WHEN $max_nodes > 0 THEN toInteger($max_nodes) ELSE 1000000000 END
    RETURN
      n.id AS id,
      n.text AS text,
      n.evidence_type AS evidence_type,
      n.source AS source,
      n.confidence AS confidence,
      n.publication_id AS publication_id
    """,
)


def _build_text(row: dict) -> str:
    return build_evidence_text(row.get("text"))


def build_evidence_generator(
    driver: Driver,
    database: str,
    config: EmbeddingConfig,
    embedder: TextEmbeddingModel,
) -> BaseEmbeddingGenerator:
    return BaseEmbeddingGenerator(
        driver=driver,
        database=database,
        config=config,
        embedder=embedder,
        label="Evidence",
        queries=EVIDENCE_QUERIES,
        text_builder=_build_text,
    )
