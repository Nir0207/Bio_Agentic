from __future__ import annotations

import pytest

from gds.app.config import Settings
from gds.projections.memory_estimation import (
    assert_estimate_safe,
    estimate_fastrp_memory,
    estimate_projection_memory,
)


class FakeClient:
    def __init__(self) -> None:
        self.last_query = ""
        self.last_params: dict = {}

    def single(self, query: str, parameters: dict | None = None) -> dict:
        self.last_query = query
        self.last_params = parameters or {}
        if "gds.graph.project.estimate" in query:
            return {
                "requiredMemory": "512 MiB",
                "bytesMin": 100,
                "bytesMax": 512 * 1024 * 1024,
                "nodeCount": 100,
                "relationshipCount": 200,
            }
        if "gds.fastRP.mutate.estimate" in query:
            return {
                "requiredMemory": "1 GiB",
                "bytesMin": 200,
                "bytesMax": 1024 * 1024 * 1024,
            }
        return {}


def test_projection_memory_estimate_uses_native_payload() -> None:
    settings = Settings(_env_file=None, gds_projection_mode="native", gds_max_memory_gb=4)
    client = FakeClient()

    result = estimate_projection_memory(client, settings)

    assert "gds.graph.project.estimate" in client.last_query
    assert result.name == "projection"
    assert result.within_threshold is True
    assert result.bytes_max == 512 * 1024 * 1024


def test_fastrp_memory_estimate_aborts_when_over_threshold() -> None:
    settings = Settings(_env_file=None, gds_max_memory_gb=0.25)
    client = FakeClient()

    result = estimate_fastrp_memory(client, settings)

    assert result.within_threshold is False
    with pytest.raises(RuntimeError):
        assert_estimate_safe(result)
