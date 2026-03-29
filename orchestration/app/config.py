from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from orchestration.app.constants import (
    DEFAULT_GRAPH_TOP_K,
    DEFAULT_MAX_GRAPH_HOPS,
    DEFAULT_MAX_GRAPH_PATHS,
    DEFAULT_SEMANTIC_TOP_K,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "orchestration/.env"),
        extra="ignore",
        populate_by_name=True,
        enable_decoding=False,
    )

    neo4j_uri: str = Field(default="bolt://host.docker.internal:7688", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="change_me", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    graph_top_k: int = Field(default=DEFAULT_GRAPH_TOP_K, alias="GRAPH_TOP_K")
    semantic_top_k: int = Field(default=DEFAULT_SEMANTIC_TOP_K, alias="SEMANTIC_TOP_K")
    max_graph_hops: int = Field(default=DEFAULT_MAX_GRAPH_HOPS, alias="MAX_GRAPH_HOPS")
    max_graph_paths: int = Field(default=DEFAULT_MAX_GRAPH_PATHS, alias="MAX_GRAPH_PATHS")

    semantic_retrieval_mode: str = Field(default="keyword", alias="SEMANTIC_RETRIEVAL_MODE")
    vector_index_name_publication: str = Field(
        default="publication_semantic_embedding_idx",
        alias="VECTOR_INDEX_NAME_PUBLICATION",
    )
    vector_index_name_evidence: str = Field(default="evidence_semantic_embedding_idx", alias="VECTOR_INDEX_NAME_EVIDENCE")

    model_score_source: str = Field(default="neo4j_property", alias="MODEL_SCORE_SOURCE")
    model_score_name: str = Field(default="target_score", alias="MODEL_SCORE_NAME")
    modeling_artifacts_dir: str = Field(default="modeling/artifacts", alias="MODELING_ARTIFACTS_DIR")

    enable_human_review: bool = Field(default=True, alias="ENABLE_HUMAN_REVIEW")
    hitl_low_confidence_threshold: float = Field(default=0.45, alias="HITL_LOW_CONFIDENCE_THRESHOLD")
    hitl_min_citations: int = Field(default=1, alias="HITL_MIN_CITATIONS")
    hitl_require_review_on_contradiction: bool = Field(default=True, alias="HITL_REQUIRE_REVIEW_ON_CONTRADICTION")
    hitl_require_review_high_stakes: bool = Field(default=True, alias="HITL_REQUIRE_REVIEW_HIGH_STAKES")
    hitl_high_stakes_terms: list[str] = Field(
        default_factory=lambda: ["life-threatening", "critical", "dose", "toxicity", "contraindication"],
        alias="HITL_HIGH_STAKES_TERMS",
    )

    allow_mock_fallback_data: bool = Field(default=True, alias="ALLOW_MOCK_FALLBACK_DATA")
    sample_query: str = Field(default="prioritize EGFR and MAPK pathway evidence", alias="SAMPLE_QUERY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("graph_top_k", "semantic_top_k", "max_graph_hops", "max_graph_paths")
    @classmethod
    def _validate_positive_int(cls, value: int) -> int:
        if int(value) < 1:
            raise ValueError("Value must be >= 1")
        return int(value)

    @field_validator("semantic_retrieval_mode", mode="before")
    @classmethod
    def _validate_semantic_mode(cls, value: Any) -> str:
        mode = str(value).strip().lower()
        if mode not in {"keyword", "vector", "hybrid"}:
            raise ValueError("SEMANTIC_RETRIEVAL_MODE must be one of: keyword, vector, hybrid")
        return mode

    @field_validator("model_score_source", mode="before")
    @classmethod
    def _validate_model_score_source(cls, value: Any) -> str:
        source = str(value).strip().lower()
        if source not in {"neo4j_property", "modeling_artifact"}:
            raise ValueError("MODEL_SCORE_SOURCE must be one of: neo4j_property, modeling_artifact")
        return source

    @field_validator("hitl_low_confidence_threshold")
    @classmethod
    def _validate_threshold(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("HITL_LOW_CONFIDENCE_THRESHOLD must be between 0 and 1")
        return float(value)

    @field_validator("hitl_high_stakes_terms", mode="before")
    @classmethod
    def _parse_csv_list(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if value is None:
            return []
        return [item.strip() for item in str(value).split(",") if item.strip()]

    @property
    def package_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def project_root(self) -> Path:
        return self.package_root.parent

    @property
    def modeling_artifacts_root(self) -> Path:
        path = Path(self.modeling_artifacts_dir)
        if path.is_absolute():
            return path
        return self.project_root / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
