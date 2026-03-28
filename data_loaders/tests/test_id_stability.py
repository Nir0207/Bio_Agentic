from __future__ import annotations

from pipelines.transforms.ids import evidence_node_id, pathway_node_id, publication_node_id, protein_node_id, stable_id


def test_ids_are_stable() -> None:
    assert stable_id("a", "b") == stable_id("a", "b")
    assert protein_node_id("P12345") == "protein:P12345"
    assert pathway_node_id("R-HSA-12345") == "pathway:R-HSA-12345"
    assert publication_node_id("123456") == "publication:123456"
    assert evidence_node_id("publication:123", "text", "abstract") == evidence_node_id(
        "publication:123", "text", "abstract"
    )

