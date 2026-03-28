from __future__ import annotations

import gzip
from pathlib import Path

import polars as pl

from pipelines.loaders.pubmed_loader import PubMedLoader

from .conftest import make_settings


def _pubmed_sample_xml() -> str:
    return """<PubmedArticleSet>
<PubmedArticle>
  <MedlineCitation>
    <PMID>1</PMID>
    <Article>
      <ArticleTitle>TP53 regulates growth</ArticleTitle>
      <Abstract>
        <AbstractText>TP53 is important in cancer.</AbstractText>
      </Abstract>
      <Journal>
        <JournalIssue>
          <PubDate><Year>2019</Year></PubDate>
        </JournalIssue>
      </Journal>
    </Article>
  </MedlineCitation>
</PubmedArticle>
</PubmedArticleSet>
"""


def test_pubmed_abstract_extraction(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, pubmed_year_min=2015)
    proteins = pl.DataFrame(
        [
            {"id": "protein:P04637", "uniprot_id": "P04637", "name": "p53", "organism": "Homo sapiens", "source": "UniProt", "reviewed": True, "string_id": "9606.ENSP1", "gene_symbol": "TP53"},
        ]
    )
    proteins.write_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")

    raw_file = settings.raw_dir / "pubmed" / "pubmed20n0001.xml.gz"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(raw_file, "wt", encoding="utf-8") as handle:
        handle.write(_pubmed_sample_xml())

    loader = PubMedLoader(settings)
    loader.load()

    publications = pl.read_parquet(settings.silver_dir / "pubmed" / "publications.parquet")
    evidence = pl.read_parquet(settings.silver_dir / "pubmed" / "evidence.parquet")
    mentions = pl.read_parquet(settings.silver_dir / "pubmed" / "publication_mentions.parquet")
    assert publications.height == 1
    assert publications.row(0, named=True)["abstract"] == "TP53 is important in cancer."
    assert evidence.height == 1
    assert mentions.height == 1

