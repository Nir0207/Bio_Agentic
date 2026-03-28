from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import Settings

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    source_name: str

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.raw_dir = settings.raw_dir / self.source_name
        self.bronze_dir = settings.bronze_dir / self.source_name
        self.silver_dir = settings.silver_dir / self.source_name
        self.bronze_dir.mkdir(parents=True, exist_ok=True)
        self.silver_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def load(self, force: bool = False) -> dict[str, Path]:
        raise NotImplementedError

