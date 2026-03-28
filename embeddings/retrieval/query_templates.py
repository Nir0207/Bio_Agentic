from __future__ import annotations

import re


VALID_SIMILARITY_FUNCTIONS = {"cosine", "euclidean", "dot"}
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_identifier(name: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(name):
        raise ValueError(f"Invalid Neo4j identifier: {name}")
    return name


def validate_similarity_function(similarity_function: str) -> str:
    normalized = similarity_function.lower()
    if normalized not in VALID_SIMILARITY_FUNCTIONS:
        supported = ", ".join(sorted(VALID_SIMILARITY_FUNCTIONS))
        raise ValueError(f"Unsupported similarity function '{similarity_function}'. Supported values: {supported}")
    return normalized


def build_vector_index_cypher(
    *,
    index_name: str,
    label: str,
    property_name: str,
    dimensions: int,
    similarity_function: str,
) -> str:
    safe_index_name = validate_identifier(index_name)
    safe_label = validate_identifier(label)
    safe_property = validate_identifier(property_name)
    safe_similarity = validate_similarity_function(similarity_function)
    if dimensions <= 0:
        raise ValueError("Vector index dimensions must be greater than zero")
    return f"""
    CREATE VECTOR INDEX {safe_index_name} IF NOT EXISTS
    FOR (n:{safe_label}) ON (n.{safe_property})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {dimensions},
        `vector.similarity_function`: '{safe_similarity}'
      }}
    }}
    """


PUBLICATION_VECTOR_SEARCH_QUERY = """
CALL db.index.vector.queryNodes($index_name, toInteger($top_k), $query_embedding)
YIELD node, score
RETURN
  node.id AS node_id,
  score AS score,
  node.title AS title,
  node.abstract AS abstract,
  node.source AS source,
  node.pmid AS pmid,
  node.pub_year AS pub_year
ORDER BY score DESC
"""


EVIDENCE_VECTOR_SEARCH_QUERY = """
CALL db.index.vector.queryNodes($index_name, toInteger($top_k), $query_embedding)
YIELD node, score
RETURN
  node.id AS node_id,
  score AS score,
  node.text AS text,
  node.source AS source,
  node.evidence_type AS evidence_type,
  node.confidence AS confidence,
  node.publication_id AS publication_id
ORDER BY score DESC
"""
