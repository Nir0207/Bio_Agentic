from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CitationKind(str, Enum):
    PUBLICATION = "publication"
    EVIDENCE_NODE = "evidence_node"
    GRAPH_PATH = "graph_path"
    MODEL_SCORE = "model_score"


class CitationEntry(BaseModel):
    citation_number: int
    citation_tag: str
    source_id: str
    source_label: str
    kind: CitationKind
    claim_ids: list[str] = Field(default_factory=list)


class CitationMap(BaseModel):
    entries: list[CitationEntry] = Field(default_factory=list)
    claim_to_tags: dict[str, list[str]] = Field(default_factory=dict)

    def tags_for_claim(self, claim_id: str) -> list[str]:
        return list(self.claim_to_tags.get(claim_id, []))
