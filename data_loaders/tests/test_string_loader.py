from __future__ import annotations

import gzip
from pathlib import Path

import polars as pl

from pipelines.loaders.string_loader import StringLoader

from .conftest import make_settings


def test_string_filtering_logic(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, string_score_threshold=700)
    proteins = pl.DataFrame(
        [
            {"id": "protein:P04637", "uniprot_id": "P04637", "name": "p53", "organism": "Homo sapiens", "source": "UniProt", "reviewed": True, "string_id": "9606.ENSP1", "gene_symbol": "TP53"},
            {"id": "protein:P38398", "uniprot_id": "P38398", "name": "BRCA1", "organism": "Homo sapiens", "source": "UniProt", "reviewed": True, "string_id": "9606.ENSP2", "gene_symbol": "BRCA1"},
        ]
    )
    proteins.write_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")

    raw_file = settings.raw_dir / "string" / "9606.protein.links.detailed.v12.0.txt.gz"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(raw_file, "wt", encoding="utf-8") as handle:
        handle.write("protein1\tprotein2\tcombined_score\n")
        handle.write("9606.ENSP1\t9606.ENSP2\t900\n")
        handle.write("9606.ENSP1\t9606.ENSP2\t600\n")

    loader = StringLoader(settings)
    loader.load()

    interactions = pl.read_parquet(settings.silver_dir / "string" / "protein_interactions.parquet")
    assert interactions.height == 1
    row = interactions.row(0, named=True)
    assert row["source_protein_id"] == "protein:P04637"
    assert row["target_protein_id"] == "protein:P38398"
    assert row["confidence"] == 900.0

