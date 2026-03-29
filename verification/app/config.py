from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from verification.app.constants import (
    DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    DEFAULT_MIN_CITATIONS_PER_CLAIM,
    DEFAULT_SAMPLE_PAYLOAD_PATH,
    HIGH_STAKES_TERMS,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "verification/.env"),
        extra="ignore",
        populate_by_name=True,
        enable_decoding=False,
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    enable_human_review: bool = Field(default=True, alias="ENABLE_HUMAN_REVIEW")
    low_confidence_threshold: float = Field(default=DEFAULT_LOW_CONFIDENCE_THRESHOLD, alias="LOW_CONFIDENCE_THRESHOLD")
    min_citations_per_claim: int = Field(default=DEFAULT_MIN_CITATIONS_PER_CLAIM, alias="MIN_CITATIONS_PER_CLAIM")
    review_on_contradiction: bool = Field(default=True, alias="REVIEW_ON_CONTRADICTION")
    review_high_stakes: bool = Field(default=True, alias="REVIEW_HIGH_STAKES")
    high_stakes_terms: list[str] = Field(default_factory=lambda: list(HIGH_STAKES_TERMS), alias="HIGH_STAKES_TERMS")
    sample_payload_path: str = Field(default=str(DEFAULT_SAMPLE_PAYLOAD_PATH), alias="SAMPLE_PAYLOAD_PATH")

    @field_validator("low_confidence_threshold")
    @classmethod
    def _validate_threshold(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("LOW_CONFIDENCE_THRESHOLD must be between 0 and 1")
        return float(value)

    @field_validator("min_citations_per_claim")
    @classmethod
    def _validate_min_citations(cls, value: int) -> int:
        if int(value) < 0:
            raise ValueError("MIN_CITATIONS_PER_CLAIM must be >= 0")
        return int(value)

    @field_validator("high_stakes_terms", mode="before")
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
    def resolved_sample_payload_path(self) -> Path:
        candidate = Path(self.sample_payload_path)
        if candidate.is_absolute():
            return candidate
        return self.project_root / candidate


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
