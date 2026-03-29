import json
from typing import Any, Generator


def sse_event(event_type: str, data: dict[str, Any]) -> str:
    return f'event: {event_type}\ndata: {json.dumps(data, ensure_ascii=True)}\n\n'


def sse_stream(events: list[tuple[str, dict[str, Any]]]) -> Generator[str, None, None]:
    for event_type, payload in events:
        yield sse_event(event_type, payload)
