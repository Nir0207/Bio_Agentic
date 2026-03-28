from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    stripped = value.strip()
    if not stripped:
        return ""
    return _WHITESPACE_RE.sub(" ", stripped)


def build_publication_text(title: str | None, abstract: str | None) -> str:
    title_clean = normalize_text(title)
    abstract_clean = normalize_text(abstract)
    if title_clean and abstract_clean:
        return f"{title_clean}\n\n{abstract_clean}"
    return title_clean or abstract_clean


def build_evidence_text(text: str | None) -> str:
    return normalize_text(text)


def chunked(items: Iterable[Any], size: int) -> Iterable[list[Any]]:
    if size <= 0:
        raise ValueError("chunk size must be greater than zero")
    batch: list[Any] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_embedding_shapes(vectors: list[list[float]], expected_dim: int | None = None) -> int:
    discovered_dim = expected_dim
    for index, vector in enumerate(vectors):
        vector_dim = len(vector)
        if vector_dim == 0:
            raise ValueError(f"Encountered empty embedding vector at index {index}")
        if discovered_dim is None:
            discovered_dim = vector_dim
            continue
        if vector_dim != discovered_dim:
            raise ValueError(
                f"Embedding dimension mismatch at index {index}: got {vector_dim}, expected {discovered_dim}"
            )
    if discovered_dim is None:
        raise ValueError("Unable to determine embedding dimension from empty vector list")
    return discovered_dim


def truncate_snippet(text: str, max_chars: int = 220) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."
