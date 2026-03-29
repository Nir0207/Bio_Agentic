from __future__ import annotations

import time
from typing import Generator

from app.integrations.orchestration_client import OrchestrationClient
from app.utils.streaming import sse_event


class OrchestrationService:
    def __init__(self) -> None:
        self.client = OrchestrationClient()

    def run(self, *, query: str, high_stakes: bool = False) -> dict:
        return self.client.run(query=query, high_stakes=high_stakes)

    def stream_run(self, *, query: str, high_stakes: bool = False) -> Generator[str, None, None]:
        payload = self.client.run(query=query, high_stakes=high_stakes)

        yield sse_event('start', {'query': query, 'stage': 'orchestration'})
        for idx, candidate in enumerate(payload.get('candidates', []), start=1):
            time.sleep(0.04)
            yield sse_event(
                'progress',
                {
                    'step': idx,
                    'message': f"Processed candidate {candidate.get('name', 'unknown')}",
                    'candidate': candidate,
                },
            )

        yield sse_event('payload', payload)
        yield sse_event('done', {'stage': 'orchestration', 'count': len(payload.get('candidates', []))})
