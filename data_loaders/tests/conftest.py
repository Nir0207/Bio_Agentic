from __future__ import annotations

from pathlib import Path

from app.config import Settings


def make_settings(tmp_path: Path, **overrides) -> Settings:
    base = dict(
        data_dir=tmp_path / "data",
        neo4j_uri="bolt://localhost:7688",
        neo4j_username="neo4j",
        neo4j_password="neo4j-password",
        neo4j_database="neo4j",
        max_pubmed_files=2,
        max_proteins=10,
        string_score_threshold=700,
        pubmed_year_min=2015,
        log_level="INFO",
    )
    base.update(overrides)
    settings = Settings(**base)
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    settings.bronze_dir.mkdir(parents=True, exist_ok=True)
    settings.silver_dir.mkdir(parents=True, exist_ok=True)
    settings.gold_dir.mkdir(parents=True, exist_ok=True)
    return settings

