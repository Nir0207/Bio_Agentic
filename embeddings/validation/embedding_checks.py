from __future__ import annotations

from neo4j import Driver

from embeddings.config import EmbeddingConfig
from embeddings.models import ValidationReport


def run_embedding_validation_checks(
    *,
    driver: Driver,
    database: str,
    config: EmbeddingConfig,
) -> ValidationReport:
    checks: dict[str, object] = {}
    warnings: list[str] = []
    critical_issues: list[str] = []

    with driver.session(database=database) as session:
        publication_embeddings = int(
            session.run(
                """
                MATCH (n:Publication)
                WHERE n.semantic_embedding IS NOT NULL
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        evidence_embeddings = int(
            session.run(
                """
                MATCH (n:Evidence)
                WHERE n.semantic_embedding IS NOT NULL
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        checks["publication_embeddings_count"] = publication_embeddings
        checks["evidence_embeddings_count"] = evidence_embeddings

        publication_missing_metadata = int(
            session.run(
                """
                MATCH (n:Publication)
                WHERE n.semantic_embedding IS NOT NULL
                  AND (n.embedding_model IS NULL OR n.embedding_dim IS NULL OR n.embedding_created_at IS NULL)
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        evidence_missing_metadata = int(
            session.run(
                """
                MATCH (n:Evidence)
                WHERE n.semantic_embedding IS NOT NULL
                  AND (n.embedding_model IS NULL OR n.embedding_dim IS NULL OR n.embedding_created_at IS NULL)
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        checks["missing_embedding_metadata"] = {
            "Publication": publication_missing_metadata,
            "Evidence": evidence_missing_metadata,
        }

        publication_inconsistent_dim = int(
            session.run(
                """
                MATCH (n:Publication)
                WHERE n.semantic_embedding IS NOT NULL
                  AND (n.embedding_dim IS NULL OR size(n.semantic_embedding) <> toInteger(n.embedding_dim))
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        evidence_inconsistent_dim = int(
            session.run(
                """
                MATCH (n:Evidence)
                WHERE n.semantic_embedding IS NOT NULL
                  AND (n.embedding_dim IS NULL OR size(n.semantic_embedding) <> toInteger(n.embedding_dim))
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        checks["inconsistent_embedding_dimensions"] = {
            "Publication": publication_inconsistent_dim,
            "Evidence": evidence_inconsistent_dim,
        }

        publication_empty_text_skipped = int(
            session.run(
                """
                MATCH (n:Publication)
                WITH n, trim(coalesce(n.title, "")) AS title, trim(coalesce(n.abstract, "")) AS abstract
                WHERE title = "" AND abstract = "" AND n.semantic_embedding IS NULL
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        evidence_empty_text_skipped = int(
            session.run(
                """
                MATCH (n:Evidence)
                WITH n, trim(coalesce(n.text, "")) AS text
                WHERE text = "" AND n.semantic_embedding IS NULL
                RETURN count(n) AS count
                """
            ).single()["count"]
        )
        checks["empty_text_records_skipped"] = {
            "Publication": publication_empty_text_skipped,
            "Evidence": evidence_empty_text_skipped,
        }

        vector_indexes = [
            record.data()
            for record in session.run(
                """
                SHOW VECTOR INDEXES
                YIELD name, state, labelsOrTypes, properties
                RETURN name, state, labelsOrTypes, properties
                """
            )
        ]
        index_map = {row["name"]: row for row in vector_indexes}
        checks["vector_index_existence"] = {
            config.publication_index_name: config.publication_index_name in index_map,
            config.evidence_index_name: config.evidence_index_name in index_map,
        }

        publication_index_search_ok, publication_index_search_error = _sample_index_query(
            session=session,
            label="Publication",
            index_name=config.publication_index_name,
        )
        evidence_index_search_ok, evidence_index_search_error = _sample_index_query(
            session=session,
            label="Evidence",
            index_name=config.evidence_index_name,
        )
        checks["sample_nearest_neighbor_search"] = {
            "Publication": publication_index_search_ok,
            "Evidence": evidence_index_search_ok,
        }

    if publication_missing_metadata > 0 or evidence_missing_metadata > 0:
        critical_issues.append("Missing embedding metadata detected on embedded nodes.")
    if publication_inconsistent_dim > 0 or evidence_inconsistent_dim > 0:
        critical_issues.append("Inconsistent embedding dimensions detected.")
    if not checks["vector_index_existence"][config.publication_index_name]:
        critical_issues.append(f"Missing vector index: {config.publication_index_name}")
    if not checks["vector_index_existence"][config.evidence_index_name]:
        critical_issues.append(f"Missing vector index: {config.evidence_index_name}")
    if not publication_index_search_ok:
        critical_issues.append(
            "Publication nearest-neighbor search check failed."
            + (f" Error: {publication_index_search_error}" if publication_index_search_error else "")
        )
    if not evidence_index_search_ok:
        critical_issues.append(
            "Evidence nearest-neighbor search check failed."
            + (f" Error: {evidence_index_search_error}" if evidence_index_search_error else "")
        )

    if publication_empty_text_skipped > 0 or evidence_empty_text_skipped > 0:
        warnings.append(
            "Some records were skipped due to empty text fields "
            f"(Publication={publication_empty_text_skipped}, Evidence={evidence_empty_text_skipped})."
        )

    return ValidationReport(checks=checks, warnings=warnings, critical_issues=critical_issues)


def _sample_index_query(*, session, label: str, index_name: str) -> tuple[bool, str | None]:
    sample = session.run(
        f"""
        MATCH (n:{label})
        WHERE n.semantic_embedding IS NOT NULL
        RETURN n.semantic_embedding AS embedding
        ORDER BY n.id ASC
        LIMIT 1
        """
    ).single()
    if sample is None:
        return False, "No embedded nodes available for sample query."

    try:
        result = session.run(
            """
            CALL db.index.vector.queryNodes($index_name, 1, $query_embedding)
            YIELD node, score
            RETURN count(node) AS matches, max(score) AS best_score
            """,
            {
                "index_name": index_name,
                "query_embedding": sample["embedding"],
            },
        ).single()
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)

    return int(result["matches"]) > 0, None
