from __future__ import annotations

import json

from answering.schemas.answer_models import FinalAnswerPayload


class JSONRenderer:
    def render(self, payload: FinalAnswerPayload) -> str:
        return json.dumps(payload.model_dump(mode="json"), indent=2)
