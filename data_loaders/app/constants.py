"""Project-wide constants."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

SOURCE_UNIPROT = "uniprot"
SOURCE_STRING = "string"
SOURCE_REACTOME = "reactome"
SOURCE_PUBMED = "pubmed"

LABEL_PROTEIN = "Protein"
LABEL_PATHWAY = "Pathway"
LABEL_PUBLICATION = "Publication"
LABEL_EVIDENCE = "Evidence"

REL_INTERACTS_WITH = "INTERACTS_WITH"
REL_PARTICIPATES_IN = "PARTICIPATES_IN"
REL_MENTIONS = "MENTIONS"
REL_HAS_EVIDENCE = "HAS_EVIDENCE"
REL_SUPPORTS = "SUPPORTS"
REL_PARENT_OF = "PARENT_OF"

RAW = "raw"
BRONZE = "bronze"
SILVER = "silver"
GOLD = "gold"

