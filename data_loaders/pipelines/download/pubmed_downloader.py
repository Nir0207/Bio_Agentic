from __future__ import annotations

from pathlib import Path

from app.config import Settings

from .base_downloader import BaseDownloader


class PubMedDownloader(BaseDownloader):
    source_name = "pubmed"
    index_url = "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def expected_files(self) -> list[Path]:
        urls = self._baseline_filenames()
        return [Path(url.split("/")[-1]) for url in urls]

    def resolve_urls(self) -> dict[Path, str]:
        filenames = self._baseline_filenames()
        resolved: dict[Path, str] = {}
        for url in filenames:
            name = Path(url.split("/")[-1])
            resolved[name] = url
        return resolved

    def _baseline_filenames(self) -> list[str]:
        urls = self._listing_urls(self.index_url)
        candidates = sorted(url for url in urls if url.endswith(".xml.gz") and "pubmed" in url.split("/")[-1])
        if not candidates:
            raise FileNotFoundError(f"No baseline files found at {self.index_url}")
        return candidates[: self.settings.max_pubmed_files]

