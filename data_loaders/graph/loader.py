from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired, TransientError

from app.config import Settings

logger = logging.getLogger(__name__)


RETRYABLE_ERRORS = (TransientError, ServiceUnavailable, SessionExpired)


@dataclass(frozen=True)
class LoadSpec:
    parquet_name: str
    cypher_file: str
    kind: str


NODE_LOAD_ORDER = [
    LoadSpec("nodes_protein.parquet", "02_load_proteins.cypher", "nodes:Protein"),
    LoadSpec("nodes_pathway.parquet", "03_load_pathways.cypher", "nodes:Pathway"),
    LoadSpec("nodes_publication.parquet", "04_load_publications.cypher", "nodes:Publication"),
    LoadSpec("nodes_evidence.parquet", "04_load_evidence.cypher", "nodes:Evidence"),
]

REL_LOAD_ORDER = [
    LoadSpec("rel_pathway_parent_of_pathway.parquet", "05_load_parent_of.cypher", "rels:PARENT_OF"),
    LoadSpec("rel_protein_participates_in_pathway.parquet", "05_load_participates.cypher", "rels:PARTICIPATES_IN"),
    LoadSpec("rel_protein_interacts_with_protein.parquet", "05_load_interacts.cypher", "rels:INTERACTS_WITH"),
    LoadSpec("rel_publication_mentions_protein.parquet", "05_load_mentions.cypher", "rels:MENTIONS"),
    LoadSpec("rel_publication_has_evidence.parquet", "05_load_has_evidence.cypher", "rels:HAS_EVIDENCE"),
    LoadSpec("rel_evidence_supports_protein.parquet", "05_load_supports.cypher", "rels:SUPPORTS"),
]


class Neo4jGraphLoader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.gold_dir = settings.gold_dir
        self.cypher_dir = Path(__file__).resolve().parent / "cypher"

    def init_constraints(self, *, dry_run: bool = False) -> None:
        self._run_cypher_file("01_constraints.cypher", dry_run=dry_run)

    def load_all(self, *, dry_run: bool = False) -> None:
        for spec in NODE_LOAD_ORDER:
            self._load_table(spec, dry_run=dry_run)
        for spec in REL_LOAD_ORDER:
            self._load_table(spec, dry_run=dry_run)

    def _driver(self):
        return GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_username, self.settings.neo4j_password),
        )

    def _read_cypher(self, filename: str) -> str:
        return (self.cypher_dir / filename).read_text(encoding="utf-8").strip()

    def _run_cypher_file(self, filename: str, parameters: dict | None = None, *, dry_run: bool = False) -> None:
        if dry_run:
            logger.info("[dry-run] Would execute cypher file: %s", filename)
            return
        cypher = self._read_cypher(filename)
        statements = [statement.strip() for statement in cypher.split(";") if statement.strip()]
        with self._driver() as driver:
            with driver.session(database=self.settings.neo4j_database) as session:
                for statement in statements:
                    self._run_with_retry(session, statement, parameters or {}, context=f"cypher:{filename}")

    def _load_table(self, spec: LoadSpec, *, dry_run: bool = False) -> None:
        path = self.gold_dir / spec.parquet_name
        if not path.exists():
            logger.warning("Skipping missing graph table %s", path)
            return
        frame = pl.read_parquet(path)
        total_rows = frame.height
        if total_rows == 0:
            logger.info("No rows to load for %s", path)
            return

        batch_size = max(1, self.settings.neo4j_batch_size)
        total_batches = (total_rows + batch_size - 1) // batch_size
        cypher = self._read_cypher(spec.cypher_file)

        if dry_run:
            logger.info(
                "[dry-run] %s would load %s rows in %s batches from %s",
                spec.kind,
                total_rows,
                total_batches,
                path,
            )
            return

        with self._driver() as driver:
            for index, batch in enumerate(frame.iter_slices(n_rows=batch_size), start=1):
                rows = batch.to_dicts()
                if not rows:
                    continue
                logger.info(
                    "Loading %s batch %s/%s (%s rows)",
                    spec.kind,
                    index,
                    total_batches,
                    len(rows),
                )
                with driver.session(database=self.settings.neo4j_database) as session:
                    self._run_with_retry(
                        session,
                        cypher,
                        {"rows": rows},
                        context=f"{spec.kind} batch {index}/{total_batches}",
                    )

        logger.info("Loaded %s rows from %s", total_rows, path)

    def _run_with_retry(self, session, cypher: str, parameters: dict, *, context: str) -> None:
        max_retries = max(1, self.settings.neo4j_max_retries)
        backoff = max(0.0, self.settings.neo4j_retry_backoff_seconds)
        for attempt in range(1, max_retries + 1):
            try:
                session.execute_write(lambda tx: tx.run(cypher, parameters).consume())
                return
            except RETRYABLE_ERRORS as exc:
                if attempt >= max_retries:
                    logger.error("Neo4j write failed after %s attempts for %s: %s", attempt, context, exc)
                    raise
                sleep_seconds = backoff * attempt
                logger.warning(
                    "Retrying Neo4j write for %s (attempt %s/%s) in %.2fs due to %s",
                    context,
                    attempt,
                    max_retries,
                    sleep_seconds,
                    exc,
                )
                if sleep_seconds:
                    time.sleep(sleep_seconds)
