from __future__ import annotations

import hashlib


def stable_id(*parts: str) -> str:
    payload = "|".join(part.strip() for part in parts if part is not None)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return digest


def protein_node_id(uniprot_id: str) -> str:
    return f"protein:{uniprot_id}"


def pathway_node_id(reactome_id: str) -> str:
    return f"pathway:{reactome_id}"


def publication_node_id(pmid: str) -> str:
    return f"publication:{pmid}"


def evidence_node_id(publication_id: str, text: str, evidence_type: str) -> str:
    return f"evidence:{stable_id(publication_id, evidence_type, text)}"

