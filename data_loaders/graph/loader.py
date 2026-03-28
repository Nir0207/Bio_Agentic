from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
from neo4j import GraphDatabase

from app.config import Settings

logger = logging.getLogger(__name__)


class Neo4jGraphLoader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.gold_dir = settings.gold_dir
        self.cypher_dir = Path(__file__).resolve().parent / "cypher"

    def init_constraints(self) -> None:
        self._run_cypher_file("01_constraints.cypher")

    def load_all(self) -> None:
        self._load_nodes("nodes_protein.parquet", "02_load_proteins.cypher")
        self._load_nodes("nodes_pathway.parquet", "03_load_pathways.cypher")
        self._load_nodes("nodes_publication.parquet", "04_load_publications.cypher")
        self._load_nodes("nodes_evidence.parquet", "04_load_evidence.cypher")
        self._load_relationships("rel_protein_interacts_with_protein.parquet", "05_load_interacts.cypher")
        self._load_relationships("rel_protein_participates_in_pathway.parquet", "05_load_participates.cypher")
        self._load_relationships("rel_publication_mentions_protein.parquet", "05_load_mentions.cypher")
        self._load_relationships("rel_publication_has_evidence.parquet", "05_load_has_evidence.cypher")
        self._load_relationships("rel_evidence_supports_protein.parquet", "05_load_supports.cypher")
        self._load_relationships("rel_pathway_parent_of_pathway.parquet", "05_load_parent_of.cypher")

    def _driver(self):
        return GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_username, self.settings.neo4j_password),
        )

    def _run_cypher_file(self, filename: str, parameters: dict | None = None) -> None:
        cypher = (self.cypher_dir / filename).read_text(encoding="utf-8")
        statements = [statement.strip() for statement in cypher.split(";") if statement.strip()]
        with self._driver() as driver:
            with driver.session(database=self.settings.neo4j_database) as session:
                for statement in statements:
                    session.run(statement, parameters or {}).consume()

    def _load_nodes(self, parquet_name: str, cypher_file: str) -> None:
        path = self.gold_dir / parquet_name
        if not path.exists():
            logger.warning("Skipping missing graph table %s", path)
            return
        df = pl.read_parquet(path)
        rows = df.to_dicts()
        self._chunked_execute(cypher_file, rows)
        logger.info("Loaded %s rows from %s", len(rows), path)

    def _load_relationships(self, parquet_name: str, cypher_file: str) -> None:
        path = self.gold_dir / parquet_name
        if not path.exists():
            logger.warning("Skipping missing relationship table %s", path)
            return
        df = pl.read_parquet(path)
        rows = df.to_dicts()
        self._chunked_execute(cypher_file, rows)
        logger.info("Loaded %s rows from %s", len(rows), path)

    def _chunked_execute(self, cypher_file: str, rows: list[dict], chunk_size: int = 1000) -> None:
        if not rows:
            return
        cypher = (self.cypher_dir / cypher_file).read_text(encoding="utf-8")
        with self._driver() as driver:
            with driver.session(database=self.settings.neo4j_database) as session:
                for start in range(0, len(rows), chunk_size):
                    batch = rows[start : start + chunk_size]
                    session.run(cypher, {"rows": batch}).consume()
