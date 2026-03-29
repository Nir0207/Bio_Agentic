from __future__ import annotations

from app.integrations.orchestration_client import OrchestrationClient
from app.integrations.verification_client import VerificationClient


class VerificationService:
    def __init__(self) -> None:
        self.orchestration_client = OrchestrationClient()
        self.verification_client = VerificationClient()

    def run(self, *, query: str | None = None, orchestration_payload: dict | None = None) -> dict:
        source_payload = orchestration_payload
        if source_payload is None and query:
            source_payload = self.orchestration_client.run(query=query)
        if source_payload is None:
            source_payload = {'query': query or 'unknown query', 'candidates': [], 'evidence_bundle': []}
        return self.verification_client.run(source_payload)
