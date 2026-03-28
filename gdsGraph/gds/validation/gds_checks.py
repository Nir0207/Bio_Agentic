from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gds.app.config import Settings
from gds.app.neo4j_client import Neo4jClient
from gds.projections.graph_projection import inspect_graph


@dataclass(frozen=True)
class GDSValidationReport:
    checks: dict[str, Any]
    warnings: list[str]
    critical_issues: list[str]
    sample_similar_proteins: list[dict[str, Any]]
    sample_communities: list[dict[str, Any]]

    @property
    def has_critical_issues(self) -> bool:
        return bool(self.critical_issues)


def run_gds_validation_checks(client: Neo4jClient, settings: Settings) -> GDSValidationReport:
    checks: dict[str, Any] = {}
    warnings: list[str] = []
    critical_issues: list[str] = []

    graph_meta = inspect_graph(client, settings.gds_graph_name)
    checks["projection_exists"] = graph_meta is not None
    checks["projected_node_count"] = graph_meta.node_count if graph_meta else 0
    checks["projected_relationship_count"] = graph_meta.relationship_count if graph_meta else 0

    if graph_meta is None:
        critical_issues.append(f"GDS graph '{settings.gds_graph_name}' does not exist in catalog")

    protein_embeddings = _single_int(
        client,
        """
        MATCH (n:Protein)
        RETURN count(n) AS total,
               sum(CASE WHEN n.graph_embedding IS NOT NULL THEN 1 ELSE 0 END) AS withEmbedding,
               sum(CASE WHEN n.graph_embedding IS NULL THEN 1 ELSE 0 END) AS withoutEmbedding
        """,
    )
    pathway_embeddings = _single_int(
        client,
        """
        MATCH (n:Pathway)
        RETURN count(n) AS total,
               sum(CASE WHEN n.graph_embedding IS NOT NULL THEN 1 ELSE 0 END) AS withEmbedding,
               sum(CASE WHEN n.graph_embedding IS NULL THEN 1 ELSE 0 END) AS withoutEmbedding
        """,
    )
    checks["protein_with_graph_embedding"] = protein_embeddings["withEmbedding"]
    checks["pathway_with_graph_embedding"] = pathway_embeddings["withEmbedding"]
    checks["protein_without_graph_embedding"] = protein_embeddings["withoutEmbedding"]
    checks["pathway_without_graph_embedding"] = pathway_embeddings["withoutEmbedding"]
    checks["null_graph_embedding_count"] = (
        protein_embeddings["withoutEmbedding"] + pathway_embeddings["withoutEmbedding"]
    )

    dim_check = _single_int(
        client,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels)
          AND n.graph_embedding IS NOT NULL
        RETURN count(n) AS embedded,
               sum(CASE WHEN size(n.graph_embedding) = $expectedDim THEN 1 ELSE 0 END) AS matchingDim,
               sum(CASE WHEN size(n.graph_embedding) = 0 THEN 1 ELSE 0 END) AS emptyVectors
        """,
        {"labels": settings.gds_node_labels, "expectedDim": settings.fastrp_embedding_dim},
    )
    checks["embedding_dimension_expected"] = settings.fastrp_embedding_dim
    checks["embedding_dimension_matching_count"] = dim_check["matchingDim"]
    checks["embedding_dimension_total_embedded"] = dim_check["embedded"]
    checks["empty_graph_embedding_count"] = dim_check["emptyVectors"]

    community_counts = _single_int(
        client,
        """
        MATCH (p:Protein)
        RETURN sum(CASE WHEN p.community_id IS NOT NULL THEN 1 ELSE 0 END) AS proteinCommunities
        """,
    )
    pathway_community_counts = _single_int(
        client,
        """
        MATCH (p:Pathway)
        RETURN sum(CASE WHEN p.community_id IS NOT NULL THEN 1 ELSE 0 END) AS pathwayCommunities
        """,
    )
    checks["protein_with_community_id"] = community_counts["proteinCommunities"]
    checks["pathway_with_community_id"] = pathway_community_counts["pathwayCommunities"]

    metadata_missing = _single_int(
        client,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels)
          AND n.graph_embedding IS NOT NULL
          AND (n.graph_embedding_model IS NULL OR n.graph_embedding_dim IS NULL OR n.graph_embedding_created_at IS NULL)
        RETURN count(n) AS missingEmbeddingMetadata
        """,
        {"labels": settings.gds_node_labels},
    )
    checks["failed_embedding_writeback_rows"] = metadata_missing["missingEmbeddingMetadata"]

    community_metadata_missing = _single_int(
        client,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels)
          AND n.community_id IS NOT NULL
          AND (n.community_algorithm IS NULL OR n.community_created_at IS NULL)
        RETURN count(n) AS missingCommunityMetadata
        """,
        {"labels": settings.gds_node_labels},
    )
    checks["failed_community_writeback_rows"] = community_metadata_missing["missingCommunityMetadata"]

    similar_count = _single_int(
        client,
        """
        MATCH (:Protein)-[r]->(:Protein)
        WHERE type(r) = $relType
        RETURN count(r) AS relCount
        """,
        {"relType": settings.knn_rel_type},
    )
    checks["similar_to_relationship_count"] = similar_count["relCount"]

    sample_similar_proteins: list[dict[str, Any]] = []
    if similar_count["relCount"] > 0:
        sample_similar_proteins = client.run(
            """
            MATCH (a:Protein)-[r]->(b:Protein)
            WHERE type(r) = $relType
            RETURN a.id AS source_id,
                   a.name AS source_name,
                   b.id AS target_id,
                   b.name AS target_name,
                   r.score AS score
            ORDER BY score DESC
            LIMIT 5
            """.strip(),
            {"relType": settings.knn_rel_type},
        )

    sample_communities = client.run(
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels)
          AND n.community_id IS NOT NULL
        RETURN n.community_id AS community_id, count(*) AS member_count
        ORDER BY member_count DESC
        LIMIT 10
        """.strip(),
        {"labels": settings.gds_node_labels},
    )

    if protein_embeddings["withEmbedding"] <= 0:
        critical_issues.append("No Protein nodes contain graph_embedding")
    if pathway_embeddings["withEmbedding"] <= 0:
        critical_issues.append("No Pathway nodes contain graph_embedding")
    if dim_check["embedded"] > 0 and dim_check["matchingDim"] != dim_check["embedded"]:
        critical_issues.append("Embedding dimensions are inconsistent across projected nodes")
    if checks["empty_graph_embedding_count"] > 0:
        warnings.append("Some nodes have empty graph_embedding vectors")
    if settings.leiden_enabled and checks["protein_with_community_id"] <= 0:
        critical_issues.append("Leiden enabled but no Protein nodes have community_id")
    if settings.leiden_enabled and checks["pathway_with_community_id"] <= 0:
        warnings.append("Leiden enabled but no Pathway nodes have community_id")
    if settings.knn_enabled and checks["similar_to_relationship_count"] <= 0:
        critical_issues.append("KNN enabled but no SIMILAR_TO relationships were created")
    if checks["failed_embedding_writeback_rows"] > 0:
        warnings.append("Some embedded nodes are missing graph embedding metadata properties")
    if checks["failed_community_writeback_rows"] > 0:
        warnings.append("Some community nodes are missing community metadata properties")

    return GDSValidationReport(
        checks=checks,
        warnings=warnings,
        critical_issues=critical_issues,
        sample_similar_proteins=sample_similar_proteins,
        sample_communities=sample_communities,
    )


def format_validation_report(report: GDSValidationReport) -> str:
    lines = ["GDS Validation", "--------------"]
    for key in sorted(report.checks.keys()):
        lines.append(f"{key}: {report.checks[key]}")

    if report.sample_similar_proteins:
        lines.append("sample_similar_proteins:")
        for row in report.sample_similar_proteins:
            lines.append(
                "  - "
                f"{row.get('source_id')} -> {row.get('target_id')} "
                f"(score={row.get('score')})"
            )

    if report.sample_communities:
        lines.append("sample_communities:")
        for row in report.sample_communities:
            lines.append(f"  - {row.get('community_id')}: {row.get('member_count')}")

    if report.warnings:
        lines.append("warnings:")
        for warning in report.warnings:
            lines.append(f"  - {warning}")

    if report.critical_issues:
        lines.append("critical_issues:")
        for issue in report.critical_issues:
            lines.append(f"  - {issue}")

    return "\n".join(lines)


def _single_int(client: Neo4jClient, query: str, params: dict[str, Any] | None = None) -> dict[str, int]:
    row = client.single(query.strip(), params or {})
    return {key: int(value or 0) for key, value in row.items()}
