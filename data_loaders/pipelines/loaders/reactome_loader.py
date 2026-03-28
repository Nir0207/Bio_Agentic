from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from app.config import Settings
from pipelines.transforms.ids import pathway_node_id
from pipelines.transforms.schemas import PATHWAY_SCHEMA, assert_schema

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class ReactomeLoader(BaseLoader):
    source_name = "reactome"

    def load(self, force: bool = False) -> dict[str, Path]:
        proteins = pl.read_parquet(self.settings.silver_dir / "uniprot" / "proteins.parquet")
        mappings = self._read_uniprot2reactome().join(
            proteins.select(pl.col("uniprot_id"), pl.col("id").alias("protein_id")),
            on="uniprot_id",
            how="inner",
        )
        bronze_path = self.bronze_dir / "reactome_mappings.parquet"
        mappings.write_parquet(bronze_path)
        logger.info("Wrote %s bronze Reactome mappings to %s", mappings.height, bronze_path)

        pathways = self._read_pathways()
        relations = self._read_relations()
        retained_pathway_ids = set(mappings.get_column("reactome_id").unique().to_list()) | set(
            relations.select("parent_pathway_id").get_column("parent_pathway_id").to_list()
        ) | set(relations.select("child_pathway_id").get_column("child_pathway_id").to_list())

        pathway_nodes = (
            pathways.filter(pl.col("reactome_id").is_in(list(retained_pathway_ids)))
            .with_columns(
                pl.col("reactome_id").map_elements(pathway_node_id, return_dtype=pl.Utf8).alias("id"),
                pl.lit("Reactome").alias("source"),
                pl.lit(None, dtype=pl.Utf8).alias("parent_pathway_id"),
            )
            .select("id", "reactome_id", "name", "species", "source", "parent_pathway_id")
            .unique(subset=["reactome_id"], keep="first")
            .sort("reactome_id")
        )
        assert_schema(pathway_nodes, PATHWAY_SCHEMA)
        pathways_path = self.silver_dir / "pathways.parquet"
        pathway_nodes.write_parquet(pathways_path)
        logger.info("Wrote %s silver pathways to %s", pathway_nodes.height, pathways_path)

        protein_pathways = (
            mappings.select(
                pl.col("protein_id"),
                pl.col("reactome_id").map_elements(pathway_node_id, return_dtype=pl.Utf8).alias("pathway_id"),
                pl.lit("Reactome").alias("source"),
                pl.lit(1.0).alias("confidence"),
                pl.lit("current").alias("dataset_version"),
            )
            .unique(subset=["protein_id", "pathway_id"], keep="first")
            .sort(["protein_id", "pathway_id"])
        )
        protein_pathways_path = self.silver_dir / "protein_pathways.parquet"
        protein_pathways.write_parquet(protein_pathways_path)
        logger.info("Wrote %s protein-pathway links to %s", protein_pathways.height, protein_pathways_path)

        relation_nodes = relations.filter(
            pl.col("parent_pathway_id").is_in(pathway_nodes.get_column("reactome_id"))
            & pl.col("child_pathway_id").is_in(pathway_nodes.get_column("reactome_id"))
        ).with_columns(
            pl.col("parent_pathway_id").map_elements(pathway_node_id, return_dtype=pl.Utf8).alias("parent_pathway_id"),
            pl.col("child_pathway_id").map_elements(pathway_node_id, return_dtype=pl.Utf8).alias("child_pathway_id"),
            pl.lit("Reactome").alias("source"),
            pl.lit(1.0).alias("confidence"),
            pl.lit("current").alias("dataset_version"),
        )
        relation_path = self.silver_dir / "pathway_parent.parquet"
        relation_nodes.write_parquet(relation_path)
        logger.info("Wrote %s pathway parent links to %s", relation_nodes.height, relation_path)

        return {
            "bronze": bronze_path,
            "pathways": pathways_path,
            "protein_pathways": protein_pathways_path,
            "pathway_parent": relation_path,
        }

    def _read_uniprot2reactome(self) -> pl.DataFrame:
        candidates = sorted(self.raw_dir.glob("UniProt2Reactome.txt"))
        if not candidates:
            raise FileNotFoundError(f"Missing UniProt2Reactome.txt in {self.raw_dir}")
        df = pl.read_csv(candidates[0], separator="\t", has_header=False)
        if df.width < 5:
            raise ValueError(f"Unexpected UniProt2Reactome schema in {candidates[0]}: width={df.width}")
        if df.width >= 6:
            df.columns = [
                "uniprot_id",
                "reactome_id",
                "reactome_url",
                "reactome_name",
                "evidence_code",
                "species",
                *[f"extra_{idx}" for idx in range(1, df.width - 5)],
            ][: df.width]
        else:
            df.columns = ["uniprot_id", "reactome_id", "reactome_name", "evidence_code", "species"]
        return df.filter(pl.col("species").str.contains("Homo sapiens", literal=True)).select(
            "uniprot_id",
            "reactome_id",
            "reactome_name",
            "evidence_code",
            "species",
        )

    def _read_pathways(self) -> pl.DataFrame:
        path = self.raw_dir / "ReactomePathways.txt"
        df = pl.read_csv(path, separator="\t", has_header=False)
        df.columns = ["reactome_id", "name", "species"]
        return df

    def _read_relations(self) -> pl.DataFrame:
        path = self.raw_dir / "ReactomePathwaysRelation.txt"
        df = pl.read_csv(path, separator="\t", has_header=False)
        df.columns = ["parent_pathway_id", "child_pathway_id"]
        return df.unique()
