from __future__ import annotations

import json
from pathlib import Path

from answering.services.citation_formatter import CitationFormatter
from answering.schemas.citation_models import CitationKind
from answering.schemas.verified_payload_models import VerifiedPayload


def _sample_payload() -> VerifiedPayload:
    path = Path(__file__).resolve().parents[1] / "payloads" / "sample_verified_payload.json"
    return VerifiedPayload.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_citation_numbering_is_stable() -> None:
    payload = _sample_payload()
    formatter = CitationFormatter()

    first = formatter.format(payload)
    second = formatter.format(payload)

    assert [item.citation_tag for item in first.entries] == [item.citation_tag for item in second.entries]
    assert first.claim_to_tags == second.claim_to_tags


def test_citation_kinds_cover_graph_publication_and_scores() -> None:
    payload = _sample_payload()
    citations = CitationFormatter().format(payload)

    kinds = {entry.kind for entry in citations.entries}
    assert CitationKind.GRAPH_PATH in kinds
    assert CitationKind.PUBLICATION in kinds
    assert CitationKind.MODEL_SCORE in kinds
