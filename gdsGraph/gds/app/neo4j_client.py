from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from .config import Settings


@dataclass
class Neo4jClient:
    uri: str
    username: str
    password: str
    database: str

    def __post_init__(self) -> None:
        self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    @classmethod
    def from_settings(cls, settings: Settings) -> "Neo4jClient":
        return cls(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> "Neo4jClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        params = parameters or {}
        with self._driver.session(database=self.database) as session:
            result = session.run(query, params)
            return [record.data() for record in result]

    def single(self, query: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        records = self.run(query, parameters)
        return records[0] if records else {}

    def verify_connectivity(self) -> None:
        try:
            self._driver.verify_connectivity()
        except Neo4jError as exc:
            raise RuntimeError(f"Failed to connect to Neo4j at {self.uri}: {exc}") from exc

    def ensure_gds_available(self) -> None:
        query = """
        SHOW PROCEDURES
        YIELD name
        WHERE name STARTS WITH 'gds.'
        RETURN count(name) AS gdsProcedureCount
        """.strip()
        row = self.single(query)
        count = int(row.get("gdsProcedureCount", 0))
        if count <= 0:
            raise RuntimeError(
                "Neo4j GDS procedures are not available on this database instance. "
                "Install/enable the Graph Data Science plugin and restart Neo4j. "
                "For Dockerized Neo4j, set NEO4J_PLUGINS='[\"graph-data-science\"]'."
            )
