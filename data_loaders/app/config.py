from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import DEFAULT_DATA_DIR, PROJECT_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    data_dir: Path = Field(default=DEFAULT_DATA_DIR, alias="DATA_DIR")
    neo4j_uri: str = Field(default="bolt://localhost:7688", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="neo4j-password", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    neo4j_batch_size: int = Field(default=2000, alias="NEO4J_BATCH_SIZE")
    neo4j_max_retries: int = Field(default=3, alias="NEO4J_MAX_RETRIES")
    neo4j_retry_backoff_seconds: float = Field(default=1.0, alias="NEO4J_RETRY_BACKOFF_SECONDS")
    max_pubmed_files: int = Field(default=5, alias="MAX_PUBMED_FILES")
    max_proteins: int = Field(default=20000, alias="MAX_PROTEINS")
    string_score_threshold: int = Field(default=700, alias="STRING_SCORE_THRESHOLD")
    pubmed_year_min: int = Field(default=2015, alias="PUBMED_YEAR_MIN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    string_download_enabled: bool = Field(default=False, alias="STRING_DOWNLOAD_ENABLED")
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")
    embedding_max_nodes: int = Field(default=0, alias="EMBEDDING_MAX_NODES")
    embedding_write_batch_size: int = Field(default=200, alias="EMBEDDING_WRITE_BATCH_SIZE")
    vector_index_name_publication: str = Field(
        default="publication_semantic_embedding_idx",
        alias="VECTOR_INDEX_NAME_PUBLICATION",
    )
    vector_index_name_evidence: str = Field(
        default="evidence_semantic_embedding_idx",
        alias="VECTOR_INDEX_NAME_EVIDENCE",
    )
    vector_similarity_function: str = Field(default="cosine", alias="VECTOR_SIMILARITY_FUNCTION")
    force_reembed: bool = Field(default=False, alias="FORCE_REEMBED")

    def resolve_data_dir(self) -> Path:
        return self.data_dir if self.data_dir.is_absolute() else PROJECT_ROOT / self.data_dir

    @property
    def raw_dir(self) -> Path:
        return self.resolve_data_dir() / "raw"

    @property
    def bronze_dir(self) -> Path:
        return self.resolve_data_dir() / "bronze"

    @property
    def silver_dir(self) -> Path:
        return self.resolve_data_dir() / "silver"

    @property
    def gold_dir(self) -> Path:
        return self.resolve_data_dir() / "gold"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
