from __future__ import annotations

import logging
from pathlib import Path

import requests

from app.config import Settings

from .base_downloader import BaseDownloader

logger = logging.getLogger(__name__)


class StringDownloader(BaseDownloader):
    source_name = "string"
    index_url = "https://string-db.org/cgi/download?species_text=Homo+sapiens"
    detailed_url = "https://stringdb-downloads.org/download/protein.links.detailed.v12.0/9606.protein.links.detailed.v12.0.txt.gz"
    aliases_url = "https://stringdb-downloads.org/download/protein.aliases.v12.0/9606.protein.aliases.v12.0.txt.gz"
    connect_timeout_seconds = 180
    read_timeout_seconds = 1200

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def expected_files(self) -> list[Path]:
        return [
            Path("9606.protein.links.detailed.v12.0.txt.gz"),
            Path("9606.protein.aliases.v12.0.txt.gz"),
        ]

    def resolve_urls(self) -> dict[Path, str]:
        return {
            Path(self.detailed_url.split("/")[-1]): self.detailed_url,
            Path(self.aliases_url.split("/")[-1]): self.aliases_url,
        }

    def download(self, force: bool = False) -> list[Path]:
        outputs: list[Path] = []
        for relative_path, url in self.resolve_urls().items():
            target = self.source_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not force:
                logger.info("Skipping existing file %s", target)
                outputs.append(target)
                continue
            try:
                self._download_without_retries(url, target)
            except requests.RequestException as exc:
                logger.warning("STRING download unavailable, skipping %s: %s", url, exc)
                continue
            if target.exists() and target.stat().st_size > 0:
                outputs.append(target)
        return outputs

    def _download_without_retries(self, url: str, target: Path) -> None:
        tmp_target = target.with_suffix(target.suffix + ".part")
        if tmp_target.exists():
            tmp_target.unlink()
        with requests.get(url, stream=True, timeout=(10, 30)) as response:
            response.raise_for_status()
            with tmp_target.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        tmp_target.replace(target)
