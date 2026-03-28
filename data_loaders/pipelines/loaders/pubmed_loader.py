from __future__ import annotations

import gzip
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import polars as pl

from app.config import Settings
from pipelines.transforms.ids import evidence_node_id, publication_node_id
from pipelines.transforms.filters import contains_any_term, year_at_least
from pipelines.transforms.schemas import EVIDENCE_SCHEMA, PUBLICATION_SCHEMA, assert_schema

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class PubMedLoader(BaseLoader):
    source_name = "pubmed"

    def load(self, force: bool = False) -> dict[str, Path]:
        raw_files = sorted(self.raw_dir.glob("*.xml.gz"))
        if not raw_files:
            raise FileNotFoundError(f"No PubMed baseline files found in {self.raw_dir}")
        rows = []
        for file in raw_files[: self.settings.max_pubmed_files]:
            rows.extend(self._parse_file(file))
        bronze = pl.DataFrame(rows) if rows else pl.DataFrame(schema={
            "pmid": pl.Utf8,
            "title": pl.Utf8,
            "abstract": pl.Utf8,
            "pub_year": pl.Int32,
        })
        bronze_path = self.bronze_dir / "pubmed_publications.parquet"
        bronze.write_parquet(bronze_path)

        publications = bronze.unique(subset=["pmid"], keep="first")
        publications = publications.filter(pl.col("abstract").is_not_null() & (pl.col("abstract") != ""))
        year_filtered = year_at_least(publications, "pub_year", self.settings.pubmed_year_min)
        if year_filtered.height == 0 and publications.height > 0:
            logger.warning(
                "PubMed year filter >= %s produced zero rows; falling back to abstract-only records.",
                self.settings.pubmed_year_min,
            )
        else:
            publications = year_filtered
        publications = self._filter_by_symbols(publications)
        publications = publications.with_columns(
            pl.col("pmid").map_elements(publication_node_id, return_dtype=pl.Utf8).alias("id"),
            pl.lit("PubMed").alias("source"),
        ).select("id", "pmid", "title", "abstract", "pub_year", "source")
        assert_schema(publications, PUBLICATION_SCHEMA)

        proteins = pl.read_parquet(self.settings.silver_dir / "uniprot" / "proteins.parquet")
        terms = self._mention_terms(proteins)
        publication_mentions = self._extract_mentions(publications, proteins, terms)

        evidence = publications.select(
            pl.col("id").alias("publication_id"),
            pl.col("abstract").alias("text"),
            pl.lit("abstract").alias("evidence_type"),
            pl.lit("PubMed").alias("source"),
            pl.lit(1.0).alias("confidence"),
        ).with_columns(
            pl.struct(["publication_id", "text", "evidence_type"]).map_elements(
                lambda row: evidence_node_id(row["publication_id"], row["text"], row["evidence_type"]),
                return_dtype=pl.Utf8,
            ).alias("id")
        ).select("id", "text", "evidence_type", "source", "confidence", "publication_id")
        assert_schema(evidence, EVIDENCE_SCHEMA)

        publication_evidence = evidence.select(
            pl.col("publication_id"),
            pl.col("id").alias("evidence_id"),
            pl.lit("PubMed").alias("source"),
            pl.lit(1.0).alias("confidence"),
            pl.lit("current").alias("dataset_version"),
        )
        evidence_supports = publication_mentions.join(publication_evidence, on="publication_id", how="inner").select(
            "evidence_id", "protein_id", "source", "confidence", "dataset_version"
        )

        publications_path = self.silver_dir / "publications.parquet"
        publications.write_parquet(publications_path)
        evidence_path = self.silver_dir / "evidence.parquet"
        evidence.write_parquet(evidence_path)
        mentions_path = self.silver_dir / "publication_mentions.parquet"
        publication_mentions.write_parquet(mentions_path)
        publication_evidence_path = self.silver_dir / "publication_evidence.parquet"
        publication_evidence.write_parquet(publication_evidence_path)
        evidence_supports_path = self.silver_dir / "evidence_supports.parquet"
        evidence_supports.write_parquet(evidence_supports_path)
        logger.info("Wrote %s bronze rows, %s publications and %s evidence rows", bronze.height, publications.height, evidence.height)
        return {
            "bronze": bronze_path,
            "publications": publications_path,
            "evidence": evidence_path,
            "publication_mentions": mentions_path,
            "publication_evidence": publication_evidence_path,
            "evidence_supports": evidence_supports_path,
        }

    def _parse_file(self, path: Path) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            context = ET.iterparse(handle, events=("end",))
            for event, elem in context:
                if elem.tag == "PubmedArticle":
                    row = self._parse_article(elem)
                    if row:
                        rows.append(row)
                    elem.clear()
        return rows

    def _parse_article(self, elem: ET.Element) -> dict[str, object] | None:
        pmid = elem.findtext(".//MedlineCitation/PMID")
        article = elem.find(".//MedlineCitation/Article")
        if pmid is None or article is None:
            return None
        title = (article.findtext("ArticleTitle") or "").strip()
        abstract_parts = [node.text.strip() for node in article.findall("Abstract/AbstractText") if node.text]
        abstract = " ".join(part for part in abstract_parts if part)
        if not abstract:
            return None
        pub_year = self._extract_year(elem)
        return {
            "pmid": pmid.strip(),
            "title": title,
            "abstract": abstract,
            "pub_year": pub_year,
        }

    def _extract_year(self, elem: ET.Element) -> int | None:
        for xpath in [
            ".//MedlineCitation/Article/Journal/JournalIssue/PubDate/Year",
            ".//MedlineCitation/Article/ArticleDate/Year",
        ]:
            year_text = elem.findtext(xpath)
            if year_text and year_text.isdigit():
                return int(year_text)
        medline_date = elem.findtext(".//MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate")
        if medline_date:
            for token in medline_date.split():
                if token[:4].isdigit():
                    return int(token[:4])
        return None

    def _mention_terms(self, proteins: pl.DataFrame) -> list[str]:
        symbols = (
            proteins.select(pl.col("gene_symbol"))
            .drop_nulls()
            .unique()
            .get_column("gene_symbol")
            .to_list()
        )
        cleaned_symbols = []
        for symbol in symbols:
            symbol = symbol.strip()
            if 2 < len(symbol) <= 12:
                cleaned_symbols.append(symbol)
        return cleaned_symbols[:2000]

    def _filter_by_symbols(self, publications: pl.DataFrame) -> pl.DataFrame:
        proteins = pl.read_parquet(self.settings.silver_dir / "uniprot" / "proteins.parquet")
        terms = [term for term in proteins.get_column("gene_symbol").drop_nulls().unique().to_list() if term and len(term) > 2]
        if not terms:
            return publications
        filtered = contains_any_term(publications, ["title", "abstract"], terms[:2000])
        if filtered.height == 0:
            logger.warning("Symbol-based PubMed filter produced zero rows; falling back to abstract-only filter.")
            return publications
        return filtered

    def _extract_mentions(self, publications: pl.DataFrame, proteins: pl.DataFrame, terms: list[str]) -> pl.DataFrame:
        if not terms:
            return pl.DataFrame(schema={
                "publication_id": pl.Utf8,
                "protein_id": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "dataset_version": pl.Utf8,
            })
        symbol_to_id_full = {
            row["gene_symbol"]: row["id"]
            for row in proteins.select("id", "gene_symbol").drop_nulls().iter_rows(named=True)
            if row["gene_symbol"]
        }
        symbol_to_id = {symbol: symbol_to_id_full[symbol] for symbol in terms if symbol in symbol_to_id_full}
        rows = []
        for row in publications.select("id", "title", "abstract").iter_rows(named=True):
            text = f"{row['title']} {row['abstract']}".lower()
            matched = [symbol for symbol in symbol_to_id if symbol.lower() in text]
            for symbol in matched:
                rows.append(
                    {
                        "publication_id": row["id"],
                        "protein_id": symbol_to_id[symbol],
                        "source": "PubMed",
                        "confidence": 0.6,
                        "dataset_version": "current",
                    }
                )
        if not rows:
            return pl.DataFrame(schema={
                "publication_id": pl.Utf8,
                "protein_id": pl.Utf8,
                "source": pl.Utf8,
                "confidence": pl.Float64,
                "dataset_version": pl.Utf8,
            })
        return pl.DataFrame(rows).unique(subset=["publication_id", "protein_id"], keep="first")
