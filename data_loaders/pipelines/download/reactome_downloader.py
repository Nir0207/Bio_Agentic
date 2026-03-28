from __future__ import annotations

from pathlib import Path

from app.config import Settings

from .base_downloader import BaseDownloader


class ReactomeDownloader(BaseDownloader):
    source_name = "reactome"
    index_url = "https://reactome.org/download/current/"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def expected_files(self) -> list[Path]:
        return [
            Path("UniProt2Reactome.txt"),
            Path("ReactomePathways.txt"),
            Path("ReactomePathwaysRelation.txt"),
        ]

    def resolve_urls(self) -> dict[Path, str]:
        filenames = [
            "UniProt2Reactome.txt",
            "ReactomePathways.txt",
            "ReactomePathwaysRelation.txt",
        ]
        urls = self._listing_urls(self.index_url)
        resolved: dict[Path, str] = {}
        for filename in filenames:
            match = next((url for url in urls if url.endswith(filename)), None)
            if match is None:
                raise FileNotFoundError(f"Could not locate {filename} in {self.index_url}")
            resolved[Path(filename)] = match
        return resolved

