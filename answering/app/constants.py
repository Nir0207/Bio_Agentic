from __future__ import annotations

from pathlib import Path

DEFAULT_SAMPLE_PAYLOAD_PATH = Path("answering/payloads/sample_verified_payload.json")
DEFAULT_ANSWER_STYLE = "technical"
DEFAULT_PROVIDER = "openai_compatible"
DEFAULT_MODEL_NAME = "gpt-5"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TIMEOUT_SECONDS = 60
FINAL_ANSWER_SCHEMA_VERSION = "1.0"
SUPPORTED_STATUSES = {"supported", "partially_supported"}
