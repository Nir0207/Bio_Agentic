from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from neo4j import GraphDatabase

from app.config import Settings

logger = logging.getLogger(__name__)


QUERY_HEADER_RE = re.compile(r"^--\s*name:\s*(?P<name>[a-zA-Z0-9_]+)\s*$")


@dataclass(frozen=True)
class RelationshipEndpointSpec:
    relationship_name: str
    parquet_name: str
    source_column: str
    source_nodes_parquet: str
    target_column: str
    target_nodes_parquet: str


REL_ENDPOINT_SPECS = [
    RelationshipEndpointSpec(
        relationship_name="INTERACTS_WITH",
        parquet_name="rel_protein_interacts_with_protein.parquet",
        source_column="source_protein_id",
        source_nodes_parquet="nodes_protein.parquet",
        target_column="target_protein_id",
        target_nodes_parquet="nodes_protein.parquet",
    ),
    RelationshipEndpointSpec(
        relationship_name="PARTICIPATES_IN",
        parquet_name="rel_protein_participates_in_pathway.parquet",
        source_column="protein_id",
        source_nodes_parquet="nodes_protein.parquet",
        target_column="pathway_id",
        target_nodes_parquet="nodes_pathway.parquet",
    ),
    RelationshipEndpointSpec(
        relationship_name="MENTIONS",
        parquet_name="rel_publication_mentions_protein.parquet",
        source_column="publication_id",
        source_nodes_parquet="nodes_publication.parquet",
        target_column="protein_id",
        target_nodes_parquet="nodes_protein.parquet",
    ),
    RelationshipEndpointSpec(
        relationship_name="HAS_EVIDENCE",
        parquet_name="rel_publication_has_evidence.parquet",
        source_column="publication_id",
        source_nodes_parquet="nodes_publication.parquet",
        target_column="evidence_id",
        target_nodes_parquet="nodes_evidence.parquet",
    ),
    RelationshipEndpointSpec(
        relationship_name="SUPPORTS",
        parquet_name="rel_evidence_supports_protein.parquet",
        source_column="evidence_id",
        source_nodes_parquet="nodes_evidence.parquet",
        target_column="protein_id",
        target_nodes_parquet="nodes_protein.parquet",
    ),
    RelationshipEndpointSpec(
        relationship_name="PARENT_OF",
        parquet_name="rel_pathway_parent_of_pathway.parquet",
        source_column="parent_pathway_id",
        source_nodes_parquet="nodes_pathway.parquet",
        target_column="child_pathway_id",
        target_nodes_parquet="nodes_pathway.parquet",
    ),
]


@dataclass
class ValidationSummary:
    query_results: dict[str, list[dict]]
    endpoint_integrity: list[dict[str, int | str]]
    warnings: list[str]
    critical_issues: list[str]

    @property
    def has_critical_issues(self) -> bool:
        return bool(self.critical_issues)


class ValidationFailedError(RuntimeError):
    pass


def load_validation_queries(query_file: Path) -> list[tuple[str, str]]:
    lines = query_file.read_text(encoding="utf-8").splitlines()
    queries: list[tuple[str, str]] = []
    current_name: str | None = None
    buffer: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        match = QUERY_HEADER_RE.match(line.strip())
        if match:
            if current_name is not None and buffer:
                query = "\n".join(buffer).strip().rstrip(";")
                queries.append((current_name, query))
            current_name = match.group("name")
            buffer = []
            continue
        if current_name is None:
            continue
        buffer.append(line)

    if current_name is not None and buffer:
        query = "\n".join(buffer).strip().rstrip(";")
        queries.append((current_name, query))

    if not queries:
        raise ValueError(f"No validation queries were found in {query_file}")
    return queries


def relationship_endpoint_integrity(gold_dir: Path) -> list[dict[str, int | str]]:
    reports: list[dict[str, int | str]] = []

    for spec in REL_ENDPOINT_SPECS:
        rel_path = gold_dir / spec.parquet_name
        src_nodes_path = gold_dir / spec.source_nodes_parquet
        dst_nodes_path = gold_dir / spec.target_nodes_parquet

        if not rel_path.exists():
            reports.append(
                {
                    "relationship": spec.relationship_name,
                    "missing_source_rows": 0,
                    "missing_target_rows": 0,
                    "missing_either_rows": 0,
                }
            )
            continue

        rel_lf = pl.scan_parquet(rel_path)
        rel_columns = rel_lf.collect_schema().names()
        expected_cols = {spec.source_column, spec.target_column}
        missing_cols = expected_cols.difference(rel_columns)
        if missing_cols:
            raise ValueError(f"Missing required columns in {rel_path}: {sorted(missing_cols)}")

        if not src_nodes_path.exists() or not dst_nodes_path.exists():
            raise FileNotFoundError(
                f"Missing required node parquet(s) for relationship check: {src_nodes_path}, {dst_nodes_path}"
            )

        src_ids = pl.read_parquet(src_nodes_path, columns=["id"]).get_column("id")
        dst_ids = pl.read_parquet(dst_nodes_path, columns=["id"]).get_column("id")

        missing_source_rows = (
            rel_lf
            .filter(~pl.col(spec.source_column).is_in(src_ids))
            .select(pl.len().alias("count"))
            .collect()
            .item()
        )
        missing_target_rows = (
            rel_lf
            .filter(~pl.col(spec.target_column).is_in(dst_ids))
            .select(pl.len().alias("count"))
            .collect()
            .item()
        )
        missing_either_rows = (
            rel_lf
            .filter(~pl.col(spec.source_column).is_in(src_ids) | ~pl.col(spec.target_column).is_in(dst_ids))
            .select(pl.len().alias("count"))
            .collect()
            .item()
        )

        reports.append(
            {
                "relationship": spec.relationship_name,
                "missing_source_rows": int(missing_source_rows),
                "missing_target_rows": int(missing_target_rows),
                "missing_either_rows": int(missing_either_rows),
            }
        )

    return reports


def _choose_sample_protein_id(gold_dir: Path) -> str | None:
    protein_nodes = gold_dir / "nodes_protein.parquet"
    if not protein_nodes.exists():
        return None
    df = pl.read_parquet(protein_nodes, columns=["id"])
    if df.height == 0:
        return None
    return df.sort("id").row(0, named=True)["id"]


def run_validations(settings: Settings, *, raise_on_critical: bool = True) -> ValidationSummary:
    query_file = Path(__file__).resolve().parent / "cypher" / "06_validation.cypher"
    query_specs = load_validation_queries(query_file)

    sample_protein_id = _choose_sample_protein_id(settings.gold_dir)
    query_results: dict[str, list[dict]] = {}

    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        with driver.session(database=settings.neo4j_database) as session:
            for name, query in query_specs:
                result = session.run(query, {"sample_protein_id": sample_protein_id})
                records = [record.data() for record in result]
                query_results[name] = records
                logger.info("Validation query '%s' returned %s rows", name, len(records))

    endpoint_integrity = relationship_endpoint_integrity(settings.gold_dir)
    warnings: list[str] = []
    critical: list[str] = []

    duplicates = query_results.get("duplicate_ids_by_label", [])
    duplicate_count = sum(int(item.get("duplicate_ids", 0) or 0) for item in duplicates)
    if duplicate_count > 0:
        critical.append(f"Found {duplicate_count} duplicate node IDs across labels.")

    endpoint_label_mismatch = query_results.get("relationship_endpoint_label_mismatches", [])
    mismatch_count = sum(int(item.get("bad_rows", 0) or 0) for item in endpoint_label_mismatch)
    if mismatch_count > 0:
        critical.append(f"Found {mismatch_count} relationships with unexpected endpoint labels.")

    for report in endpoint_integrity:
        missing_rows = int(report["missing_either_rows"])
        if missing_rows > 0:
            critical.append(
                f"Relationship {report['relationship']} has {missing_rows} rows with missing endpoints in gold tables."
            )

    orphan_publications = query_results.get("orphan_publications", [])
    orphan_publications_count = int(orphan_publications[0].get("orphan_publications", 0)) if orphan_publications else 0
    if orphan_publications_count > 0:
        warnings.append(f"Found {orphan_publications_count} orphan Publication nodes.")

    orphan_evidence = query_results.get("orphan_evidence", [])
    orphan_evidence_count = int(orphan_evidence[0].get("orphan_evidence", 0)) if orphan_evidence else 0
    if orphan_evidence_count > 0:
        warnings.append(f"Found {orphan_evidence_count} orphan Evidence nodes.")

    empty_abstract_rows = query_results.get("publications_with_empty_abstract", [])
    empty_abstract_count = int(empty_abstract_rows[0].get("empty_abstract_publications", 0)) if empty_abstract_rows else 0
    if empty_abstract_count > 0:
        warnings.append(f"Found {empty_abstract_count} Publication nodes with empty abstracts after load.")

    summary = ValidationSummary(
        query_results=query_results,
        endpoint_integrity=endpoint_integrity,
        warnings=warnings,
        critical_issues=critical,
    )

    logger.info("Validation summary: %s critical issue(s), %s warning(s)", len(critical), len(warnings))

    if raise_on_critical and summary.has_critical_issues:
        raise ValidationFailedError("; ".join(summary.critical_issues))

    return summary
