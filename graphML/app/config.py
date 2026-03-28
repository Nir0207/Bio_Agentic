from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import DEFAULT_NODE_LABELS, DEFAULT_RELATIONSHIP_TYPES, SUPPORTED_PROJECTION_MODES


class Settings(BaseSettings):
    # Keep env parsing compatible with CSV-style list vars in .env/.env.example
    # (for example: GDS_NODE_LABELS=Protein,Pathway) instead of requiring JSON arrays.
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
        enable_decoding=False,
    )

    neo4j_uri: str = Field(default="bolt://host.docker.internal:7688", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="change_me", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    gds_graph_name: str = Field(default="protein_pathway_graph", alias="GDS_GRAPH_NAME")
    gds_replace_graph: bool = Field(default=False, alias="GDS_REPLACE_GRAPH")
    gds_projection_mode: str = Field(default="auto", alias="GDS_PROJECTION_MODE")
    gds_node_labels: list[str] = Field(default_factory=lambda: list(DEFAULT_NODE_LABELS), alias="GDS_NODE_LABELS")
    gds_relationship_types: list[str] = Field(
        default_factory=lambda: list(DEFAULT_RELATIONSHIP_TYPES),
        alias="GDS_RELATIONSHIP_TYPES",
    )
    gds_max_memory_gb: float = Field(default=4.0, alias="GDS_MAX_MEMORY_GB")

    fastrp_embedding_dim: int = Field(default=256, alias="FASTRP_EMBEDDING_DIM")
    fastrp_iteration_weights: list[float] = Field(default_factory=lambda: [0.0, 1.0, 1.0], alias="FASTRP_ITERATION_WEIGHTS")
    fastrp_normalization_strength: float = Field(default=0.0, alias="FASTRP_NORMALIZATION_STRENGTH")

    leiden_enabled: bool = Field(default=True, alias="LEIDEN_ENABLED")
    leiden_max_levels: int = Field(default=10, alias="LEIDEN_MAX_LEVELS")

    knn_enabled: bool = Field(default=False, alias="KNN_ENABLED")
    knn_top_k: int = Field(default=10, alias="KNN_TOP_K")
    knn_similarity_cutoff: float = Field(default=0.7, alias="KNN_SIMILARITY_CUTOFF")
    knn_rel_type: str = Field(default="SIMILAR_TO", alias="KNN_REL_TYPE")
    knn_node_labels: list[str] = Field(default_factory=lambda: ["Protein"], alias="KNN_NODE_LABELS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("gds_projection_mode", mode="before")
    @classmethod
    def _validate_projection_mode(cls, value: Any) -> str:
        mode = str(value).strip().lower()
        if mode not in SUPPORTED_PROJECTION_MODES:
            raise ValueError(f"Unsupported GDS_PROJECTION_MODE={value}. Use one of: {sorted(SUPPORTED_PROJECTION_MODES)}")
        return mode

    @field_validator("gds_node_labels", "gds_relationship_types", "knn_node_labels", mode="before")
    @classmethod
    def _parse_csv_list(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if value is None:
            return []
        return [item.strip() for item in str(value).split(",") if item.strip()]

    @field_validator("fastrp_iteration_weights", mode="before")
    @classmethod
    def _parse_float_csv(cls, value: Any) -> list[float]:
        if isinstance(value, list):
            return [float(v) for v in value]
        if value is None or str(value).strip() == "":
            return [0.0, 1.0, 1.0]
        return [float(item.strip()) for item in str(value).split(",") if item.strip()]

    @field_validator("gds_node_labels")
    @classmethod
    def _ensure_node_labels(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("GDS_NODE_LABELS cannot be empty")
        return value

    @field_validator("gds_relationship_types")
    @classmethod
    def _ensure_relationship_types(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("GDS_RELATIONSHIP_TYPES cannot be empty")
        return value

    @field_validator("knn_node_labels")
    @classmethod
    def _ensure_knn_node_labels(cls, value: list[str]) -> list[str]:
        return value or ["Protein"]

    @property
    def gds_max_memory_bytes(self) -> int:
        return int(self.gds_max_memory_gb * 1024**3)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
