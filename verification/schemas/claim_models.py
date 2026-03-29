from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    ENTITY_ASSOCIATION = "entity_association"
    PATHWAY_PARTICIPATION = "pathway_participation"
    SIMILARITY_CLAIM = "similarity_claim"
    EVIDENCE_STRENGTH_CLAIM = "evidence_strength_claim"
    RANKING_CLAIM = "ranking_claim"


class DirectnessLevel(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    UNSPECIFIED = "unspecified"


class SourceSpan(BaseModel):
    start_char: int
    end_char: int
    text: str


class ExtractedClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    target_entity_ids: list[str] = Field(default_factory=list)
    directness_level: DirectnessLevel = DirectnessLevel.UNSPECIFIED
    source_span: SourceSpan | None = None
    referenced_citation_ids: list[str] = Field(default_factory=list)
    referenced_score_ids: list[str] = Field(default_factory=list)
    critical: bool = False
