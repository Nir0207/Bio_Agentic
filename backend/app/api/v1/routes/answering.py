from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_answering_service, get_current_user
from app.schemas.answering import AnsweringRequest, AnsweringResponse
from app.services.answering_service import AnsweringService
from app.utils.response_builder import ResponseBuilder
from app.utils.streaming import sse_event

router = APIRouter(prefix='/answering', tags=['answering'])


@router.post('/run', response_model=AnsweringResponse)
def run(
    payload: AnsweringRequest,
    service: AnsweringService = Depends(get_answering_service),
    _=Depends(get_current_user),
) -> AnsweringResponse:
    result = service.run(query=payload.query, verified_payload=payload.verified_payload, style=payload.style)
    return AnsweringResponse(payload=result)


@router.post('/stream')
def stream(
    payload: AnsweringRequest,
    service: AnsweringService = Depends(get_answering_service),
    _=Depends(get_current_user),
) -> StreamingResponse:
    def event_generator():
        try:
            yield from service.stream_run(query=payload.query, verified_payload=payload.verified_payload, style=payload.style)
        except Exception as exc:  # pragma: no cover - handled at runtime
            yield sse_event('error', ResponseBuilder.success({'details': str(exc)}, message='stream_error'))

    return StreamingResponse(event_generator(), media_type='text/event-stream')
