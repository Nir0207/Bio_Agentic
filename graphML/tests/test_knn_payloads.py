from __future__ import annotations

from graphML.algorithms.knn_runner import build_knn_write_config
from graphML.app.config import Settings


def test_knn_payload_respects_topk_cutoff_reltype_and_labels() -> None:
    settings = Settings(
        _env_file=None,
        knn_top_k=25,
        knn_similarity_cutoff=0.81,
        knn_rel_type="SIMILAR_TO",
        knn_node_labels="Protein,Pathway",
    )

    payload = build_knn_write_config(settings)

    assert payload["nodeProperties"] == ["graph_embedding"]
    assert payload["topK"] == 25
    assert payload["similarityCutoff"] == 0.81
    assert payload["writeRelationshipType"] == "SIMILAR_TO"
    assert payload["writeProperty"] == "score"
    assert payload["nodeLabels"] == ["Protein", "Pathway"]
