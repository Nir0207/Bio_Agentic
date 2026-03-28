from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

IntentType = Literal[
    "target_prioritization",
    "pathway_exploration",
    "evidence_lookup",
    "similarity_lookup",
]


class QueryInput(BaseModel):
    text: str = Field(min_length=1)
    high_stakes: bool = False


class NormalizedQuery(BaseModel):
    raw_text: str
    normalized_text: str
    tokens: list[str] = Field(default_factory=list)
    entity_mentions: list[str] = Field(default_factory=list)
