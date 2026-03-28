from __future__ import annotations

from embeddings.utils import build_evidence_text, build_publication_text, chunked, normalize_text


def test_chunked_splits_in_deterministic_order() -> None:
    values = [1, 2, 3, 4, 5]
    chunks = list(chunked(values, 2))
    assert chunks == [[1, 2], [3, 4], [5]]


def test_publication_text_uses_title_and_abstract_with_fallback() -> None:
    full = build_publication_text("  A title ", "  An abstract  ")
    title_only = build_publication_text("  A title ", " ")
    empty = build_publication_text(" ", None)

    assert full == "A title\n\nAn abstract"
    assert title_only == "A title"
    assert empty == ""


def test_normalize_and_evidence_text_clean_whitespace() -> None:
    assert normalize_text("  alpha   beta\tgamma\n") == "alpha beta gamma"
    assert build_evidence_text("  evidence   line ") == "evidence line"
