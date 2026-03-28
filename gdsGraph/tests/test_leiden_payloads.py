from __future__ import annotations

from gds.algorithms.leiden_runner import build_leiden_write_config
from gds.app.config import Settings


def test_leiden_payload_uses_configured_levels() -> None:
    settings = Settings(_env_file=None, leiden_max_levels=15)

    payload = build_leiden_write_config(settings)

    assert payload == {
        "writeProperty": "community_id",
        "maxLevels": 15,
    }
