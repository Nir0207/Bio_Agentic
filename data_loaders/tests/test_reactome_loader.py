from __future__ import annotations

from pathlib import Path

import polars as pl

from pipelines.loaders.reactome_loader import ReactomeLoader

from .conftest import make_settings


def test_reactome_loader_filters_to_retained_proteins(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    proteins = pl.DataFrame(
        [
            {"id": "protein:P04637", "uniprot_id": "P04637", "name": "p53", "organism": "Homo sapiens", "source": "UniProt", "reviewed": True, "string_id": "9606.ENSP1", "gene_symbol": "TP53"},
        ]
    )
    proteins.write_parquet(settings.silver_dir / "uniprot" / "proteins.parquet")

    raw_dir = settings.raw_dir / "reactome"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "UniProt2Reactome.txt").write_text(
        "P04637\tR-HSA-1\tTP53 signaling\tIEA\tHomo sapiens\nP99999\tR-HSA-2\tOther\tIEA\tHomo sapiens\n",
        encoding="utf-8",
    )
    (raw_dir / "ReactomePathways.txt").write_text(
        "R-HSA-1\tTP53 signaling\tHomo sapiens\nR-HSA-2\tOther\tHomo sapiens\n",
        encoding="utf-8",
    )
    (raw_dir / "ReactomePathwaysRelation.txt").write_text(
        "R-HSA-1\tR-HSA-2\n",
        encoding="utf-8",
    )

    loader = ReactomeLoader(settings)
    loader.load()

    pathways = pl.read_parquet(settings.silver_dir / "reactome" / "pathways.parquet")
    assert pathways.height == 2
    protein_pathways = pl.read_parquet(settings.silver_dir / "reactome" / "protein_pathways.parquet")
    assert protein_pathways.height == 1
    assert protein_pathways.row(0, named=True)["protein_id"] == "protein:P04637"

