from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CandidateEntity(BaseModel):
    candidate_id: str
    candidate_type: Literal["Protein", "Pathway", "Publication", "Evidence", "Unknown"] = "Unknown"
    display_name: str | None = None
    sources: list[str] = Field(default_factory=list)
    graph_support: float = 0.0
    semantic_support: float = 0.0
    model_support: float = 0.0
    rank_score: float = 0.0
    attributes: dict[str, Any] = Field(default_factory=dict)
