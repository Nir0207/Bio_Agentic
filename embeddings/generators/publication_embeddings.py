from __future__ import annotations

from neo4j import Driver

from embeddings.config import EmbeddingConfig
from embeddings.generators.base_generator import BaseEmbeddingGenerator, GeneratorQueries
from embeddings.registry import TextEmbeddingModel
from embeddings.utils import build_publication_text


PUBLICATION_QUERIES = GeneratorQueries(
    count_total="""
    MATCH (n:Publication)
    RETURN count(n) AS count
    """,
    count_already_embedded="""
    MATCH (n:Publication)
    WHERE n.semantic_embedding IS NOT NULL
    RETURN count(n) AS count
    """,
    fetch_candidates="""
    MATCH (n:Publication)
    WHERE $force OR n.semantic_embedding IS NULL
    WITH n
    ORDER BY n.id ASC
    LIMIT CASE WHEN $max_nodes > 0 THEN toInteger($max_nodes) ELSE 1000000000 END
    RETURN
      n.id AS id,
      n.title AS title,
      n.abstract AS abstract,
      n.pmid AS pmid,
      n.source AS source,
      n.pub_year AS pub_year
    """,
)


def _build_text(row: dict) -> str:
    return build_publication_text(row.get("title"), row.get("abstract"))


def build_publication_generator(
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
        label="Publication",
        queries=PUBLICATION_QUERIES,
        text_builder=_build_text,
    )
