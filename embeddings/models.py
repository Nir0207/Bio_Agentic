from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EmbeddingInput:
    node_id: str
    text: str
    source_metadata: dict[str, Any]


@dataclass(frozen=True)
class EmbeddingRecord:
    node_id: str
    embedding: list[float]
    embedding_model: str
    embedding_dim: int
    embedding_created_at: str


@dataclass(frozen=True)
class GenerationStats:
    label: str
    total_nodes: int
    already_embedded: int
    candidates: int
    processed: int
    skipped: int
    failed: int
    empty_text_skipped: int


@dataclass(frozen=True)
class SearchResult:
    node_id: str
    label: str
    score: float
    snippet: str
    source_metadata: dict[str, Any]


@dataclass(frozen=True)
class ValidationReport:
    checks: dict[str, Any]
    warnings: list[str]
    critical_issues: list[str]

    @property
    def has_critical_issues(self) -> bool:
        return bool(self.critical_issues)
