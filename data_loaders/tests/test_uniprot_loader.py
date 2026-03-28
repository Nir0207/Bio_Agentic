from __future__ import annotations

import gzip
from pathlib import Path

import polars as pl

from pipelines.loaders.uniprot_loader import UniProtLoader

from .conftest import make_settings


def _write_uniprot_sample(path: Path) -> None:
    content = """Entry\tProtein names\tOrganism\tReviewed\tGene Names (primary)\tCross-reference (STRING)
P04637\tCellular tumor antigen p53\tHomo sapiens (Human)\treviewed\tTP53\tSTRING; 9606.ENSP00000269305;
Q00001\tMouse protein\tMus musculus (Mouse)\treviewed\tMouse1\t
"""
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(content)


def test_uniprot_column_normalization_and_filtering(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, max_proteins=5)
    raw_file = settings.raw_dir / "uniprot" / "uniprot_human_reviewed.tsv.gz"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    _write_uniprot_sample(raw_file)

    loader = UniProtLoader(settings)
    loader.load()

    proteins = pl.read_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")
    assert proteins.height == 1
    row = proteins.row(0, named=True)
    assert row["uniprot_id"] == "P04637"
    assert row["gene_symbol"] == "TP53"
    assert row["reviewed"] is True
    assert row["organism"].startswith("Homo sapiens")
