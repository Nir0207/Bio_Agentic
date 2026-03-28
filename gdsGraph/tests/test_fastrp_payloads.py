from __future__ import annotations

from gds.algorithms.fastrp_runner import build_fastrp_write_config
from gds.app.config import Settings


def test_fastrp_payload_uses_configured_dimension_and_weights() -> None:
    settings = Settings(
        _env_file=None,
        fastrp_embedding_dim=128,
        fastrp_iteration_weights="0.0,0.5,1.0",
        fastrp_normalization_strength=0.25,
    )

    payload = build_fastrp_write_config(settings)

    assert payload["embeddingDimension"] == 128
    assert payload["iterationWeights"] == [0.0, 0.5, 1.0]
    assert payload["normalizationStrength"] == 0.25
    assert payload["mutateProperty"] == "graph_embedding"
