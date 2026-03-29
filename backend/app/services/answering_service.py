from __future__ import annotations

import time
from typing import Generator

from app.integrations.answering_client import AnsweringClient
from app.services.verification_service import VerificationService
from app.utils.streaming import sse_event


class AnsweringService:
    def __init__(self) -> None:
        self.answering_client = AnsweringClient()
        self.verification_service = VerificationService()

    def run(self, *, query: str | None = None, verified_payload: dict | None = None, style: str = 'concise') -> dict:
        base_payload = verified_payload
        if base_payload is None and query:
            base_payload = self.verification_service.run(query=query)
        if base_payload is None:
            base_payload = {'overall_verdict': 'unknown', 'overall_confidence': 0.0, 'citations': []}
        return self.answering_client.run(base_payload, style=style)

    def stream_run(
        self,
        *,
        query: str | None = None,
        verified_payload: dict | None = None,
        style: str = 'concise',
    ) -> Generator[str, None, None]:
        final_payload = self.run(query=query, verified_payload=verified_payload, style=style)
        answer_text = final_payload.get('answer_text', '')

        yield sse_event('start', {'stage': 'answering', 'style': style})
        yield sse_event('progress', {'message': 'Constructing final answer from verified evidence.'})

        words = answer_text.split()
        partial = []
        for index, word in enumerate(words, start=1):
            partial.append(word)
            if index % 5 == 0 or index == len(words):
                time.sleep(0.04)
                yield sse_event('partial_text', {'text': ' '.join(partial)})

        yield sse_event('payload', final_payload)
        yield sse_event('done', {'stage': 'answering'})
