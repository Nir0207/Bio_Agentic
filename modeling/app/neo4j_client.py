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

    def verify_connectivity(self) -> None:
        try:
            self._driver.verify_connectivity()
        except Neo4jError as exc:
            raise RuntimeError(f"Failed to connect to Neo4j at {self.uri}: {exc}") from exc
