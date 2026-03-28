from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import Settings

logger = logging.getLogger(__name__)


class BaseDownloader(ABC):
    source_name: str
    connect_timeout_seconds = 120
    read_timeout_seconds = 900

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.source_dir = settings.raw_dir / self.source_name
        self.source_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def expected_files(self) -> list[Path]:
        raise NotImplementedError

    @abstractmethod
    def resolve_urls(self) -> dict[Path, str]:
        raise NotImplementedError

    def download(self, force: bool = False) -> list[Path]:
        outputs: list[Path] = []
        urls = self.resolve_urls()
        for relative_path, url in urls.items():
            target = self.source_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not force:
                logger.info("Skipping existing file %s", target)
                outputs.append(target)
                continue
            logger.info("Downloading %s -> %s", url, target)
            self._download_file(url, target)
            if not target.exists() or target.stat().st_size == 0:
                raise FileNotFoundError(f"Download failed for {target}")
            outputs.append(target)
        return outputs

    def _download_file(self, url: str, target: Path) -> None:
        session = requests.Session()
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "HEAD"}),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        tmp_target = target.with_suffix(target.suffix + ".part")
        if tmp_target.exists():
            tmp_target.unlink()
        try:
            with session.get(
                url,
                stream=True,
                timeout=(self.connect_timeout_seconds, self.read_timeout_seconds),
            ) as response:
                response.raise_for_status()
                with tmp_target.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            tmp_target.replace(target)
        finally:
            session.close()
            if tmp_target.exists() and not target.exists():
                tmp_target.unlink(missing_ok=True)

    def _listing_urls(self, index_url: str) -> list[str]:
        response = requests.get(index_url, timeout=300)
        response.raise_for_status()
        hrefs = re.findall(r'href="([^"]+)"', response.text, flags=re.IGNORECASE)
        urls = [urljoin(index_url, href) for href in hrefs if not href.startswith("?")]
        return urls

    def _first_matching_url(self, index_url: str, patterns: list[str]) -> str:
        urls = self._listing_urls(index_url)
        for pattern in patterns:
            regex = re.compile(pattern, flags=re.IGNORECASE)
            for url in urls:
                if regex.search(url):
                    return url
        raise FileNotFoundError(f"No URL matched {patterns!r} under {index_url}")
