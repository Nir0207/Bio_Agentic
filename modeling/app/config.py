from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import SUPPORTED_LABEL_STRATEGIES, SUPPORTED_MODEL_TYPES, SUPPORTED_TASK_TYPES


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        populate_by_name=True,
    )

    neo4j_uri: str = Field(default="bolt://host.docker.internal:7688", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="change_me", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    mlflow_tracking_uri: str = Field(default="http://host.docker.internal:5000", alias="MLFLOW_TRACKING_URI")
    mlflow_experiment_name: str = Field(default="pharma_graph_modeling", alias="MLFLOW_EXPERIMENT_NAME")
    mlflow_register_model: bool = Field(default=True, alias="MLFLOW_REGISTER_MODEL")
    model_registry_name: str = Field(default="protein_target_model", alias="MODEL_REGISTRY_NAME")
    model_registry_alias: str = Field(default="latest", alias="MODEL_REGISTRY_ALIAS")

    model_type: str = Field(default="logistic_regression", alias="MODEL_TYPE")
    task_type: str = Field(default="classification", alias="TASK_TYPE")
    label_strategy: str = Field(default="heuristic_binary", alias="LABEL_STRATEGY")

    train_test_seed: int = Field(default=42, alias="TRAIN_TEST_SEED")
    test_size: float = Field(default=0.2, alias="TEST_SIZE")
    validation_size: float = Field(default=0.1, alias="VALIDATION_SIZE")

    heuristic_positive_percentile: float = Field(default=0.2, alias="HEURISTIC_POSITIVE_PERCENTILE")
    heuristic_weight_evidence_count: float = Field(default=0.35, alias="HEURISTIC_WEIGHT_EVIDENCE_COUNT")
    heuristic_weight_avg_evidence_confidence: float = Field(default=0.25, alias="HEURISTIC_WEIGHT_AVG_CONFIDENCE")
    heuristic_weight_pathway_count: float = Field(default=0.15, alias="HEURISTIC_WEIGHT_PATHWAY_COUNT")
    heuristic_weight_interaction_count: float = Field(default=0.15, alias="HEURISTIC_WEIGHT_INTERACTION_COUNT")
    heuristic_weight_publication_count: float = Field(default=0.05, alias="HEURISTIC_WEIGHT_PUBLICATION_COUNT")
    heuristic_weight_max_evidence_confidence: float = Field(default=0.05, alias="HEURISTIC_WEIGHT_MAX_CONFIDENCE")

    enable_xgboost: bool = Field(default=False, alias="ENABLE_XGBOOST")
    writeback_scores: bool = Field(default=False, alias="WRITEBACK_SCORES")
    writeback_batch_size: int = Field(default=500, alias="WRITEBACK_BATCH_SIZE")

    dataset_chunk_size: int = Field(default=25000, alias="DATASET_CHUNK_SIZE")
    artifacts_dir: str = Field(default="artifacts", alias="ARTIFACTS_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("model_type", mode="before")
    @classmethod
    def _validate_model_type(cls, value: Any) -> str:
        model_type = str(value).strip().lower()
        if model_type not in SUPPORTED_MODEL_TYPES:
            raise ValueError(f"Unsupported MODEL_TYPE={value}. Use one of: {sorted(SUPPORTED_MODEL_TYPES)}")
        return model_type

    @field_validator("task_type", mode="before")
    @classmethod
    def _validate_task_type(cls, value: Any) -> str:
        task_type = str(value).strip().lower()
        if task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(f"Unsupported TASK_TYPE={value}. Use one of: {sorted(SUPPORTED_TASK_TYPES)}")
        return task_type

    @field_validator("label_strategy", mode="before")
    @classmethod
    def _validate_label_strategy(cls, value: Any) -> str:
        strategy = str(value).strip().lower()
        if strategy not in SUPPORTED_LABEL_STRATEGIES:
            raise ValueError(f"Unsupported LABEL_STRATEGY={value}. Use one of: {sorted(SUPPORTED_LABEL_STRATEGIES)}")
        return strategy

    @field_validator("test_size", "validation_size")
    @classmethod
    def _validate_split_size(cls, value: float) -> float:
        if value <= 0 or value >= 1:
            raise ValueError("Split sizes must be within (0, 1)")
        return value

    @field_validator("heuristic_positive_percentile")
    @classmethod
    def _validate_positive_percentile(cls, value: float) -> float:
        if value <= 0 or value >= 1:
            raise ValueError("HEURISTIC_POSITIVE_PERCENTILE must be within (0, 1)")
        return value

    @property
    def package_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def artifacts_root(self) -> Path:
        configured = Path(self.artifacts_dir)
        if configured.is_absolute():
            return configured
        return self.package_root / configured

    @property
    def heuristic_weights(self) -> dict[str, float]:
        return {
            "evidence_count": self.heuristic_weight_evidence_count,
            "avg_evidence_confidence": self.heuristic_weight_avg_evidence_confidence,
            "pathway_count": self.heuristic_weight_pathway_count,
            "interaction_count": self.heuristic_weight_interaction_count,
            "publication_count": self.heuristic_weight_publication_count,
            "max_evidence_confidence": self.heuristic_weight_max_evidence_confidence,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
