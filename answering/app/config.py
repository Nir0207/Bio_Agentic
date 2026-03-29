from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from answering.app.constants import (
    DEFAULT_ANSWER_STYLE,
    DEFAULT_MODEL_NAME,
    DEFAULT_PROVIDER,
    DEFAULT_SAMPLE_PAYLOAD_PATH,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
)
from answering.schemas.answer_models import AnswerStyle


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        populate_by_name=True,
        enable_decoding=False,
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    answer_style: AnswerStyle = Field(default=AnswerStyle(DEFAULT_ANSWER_STYLE), alias="ANSWER_STYLE")
    answering_provider: str = Field(default=DEFAULT_PROVIDER, alias="ANSWERING_PROVIDER")
    answering_model_name: str = Field(default=DEFAULT_MODEL_NAME, alias="ANSWERING_MODEL_NAME")
    answering_temperature: float = Field(default=DEFAULT_TEMPERATURE, alias="ANSWERING_TEMPERATURE")
    answering_timeout_seconds: int = Field(default=DEFAULT_TIMEOUT_SECONDS, alias="ANSWERING_TIMEOUT_SECONDS")
    answering_use_fallback_only: bool = Field(default=False, alias="ANSWERING_USE_FALLBACK_ONLY")

    answering_base_url: str | None = Field(default=None, alias="ANSWERING_BASE_URL")
    answering_api_key: str | None = Field(default=None, alias="ANSWERING_API_KEY")

    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(default="2024-10-21", alias="AZURE_OPENAI_API_VERSION")

    anthropic_base_url: str | None = Field(default=None, alias="ANTHROPIC_BASE_URL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    ollama_base_url: str = Field(default="http://host.docker.internal:11434", alias="OLLAMA_BASE_URL")

    enable_optional_enrichment: bool = Field(default=False, alias="ENABLE_OPTIONAL_ENRICHMENT")
    neo4j_uri: str = Field(default="bolt://host.docker.internal:7688", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="change_me", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    sample_payload_path: str = Field(default=str(DEFAULT_SAMPLE_PAYLOAD_PATH), alias="SAMPLE_VERIFIED_PAYLOAD_PATH")
    max_retries: int = Field(default=2, alias="ANSWERING_MAX_RETRIES")

    @field_validator("answering_temperature")
    @classmethod
    def _validate_temperature(cls, value: float) -> float:
        numeric = float(value)
        if numeric < 0 or numeric > 2:
            raise ValueError("ANSWERING_TEMPERATURE must be between 0 and 2")
        return numeric

    @field_validator("answering_timeout_seconds")
    @classmethod
    def _validate_timeout(cls, value: int) -> int:
        timeout = int(value)
        if timeout <= 0:
            raise ValueError("ANSWERING_TIMEOUT_SECONDS must be > 0")
        return timeout

    @field_validator("answering_provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("answer_style", mode="before")
    @classmethod
    def _normalize_style(cls, value: str | AnswerStyle) -> AnswerStyle:
        if isinstance(value, AnswerStyle):
            return value
        return AnswerStyle(str(value).strip().lower())

    @property
    def package_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def project_root(self) -> Path:
        return self.package_root.parent

    @property
    def resolved_sample_payload_path(self) -> Path:
        candidate = Path(self.sample_payload_path)
        if candidate.is_absolute():
            return candidate
        return self.project_root / candidate


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
