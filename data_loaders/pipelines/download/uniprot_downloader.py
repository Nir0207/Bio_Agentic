from __future__ import annotations

from pathlib import Path

from app.config import Settings

from .base_downloader import BaseDownloader


class UniProtDownloader(BaseDownloader):
    source_name = "uniprot"
    source_url = (
        "https://rest.uniprot.org/uniprotkb/stream"
        "?query=reviewed:true%20AND%20organism_id:9606"
        "&format=tsv"
        "&compressed=true"
        "&fields=accession,id,protein_name,gene_primary,organism_name,reviewed,xref_string"
    )

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def expected_files(self) -> list[Path]:
        return [Path("uniprot_human_reviewed.tsv.gz")]

    def resolve_urls(self) -> dict[Path, str]:
        return {Path("uniprot_human_reviewed.tsv.gz"): self.source_url}
