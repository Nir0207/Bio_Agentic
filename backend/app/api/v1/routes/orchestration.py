from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_user, get_orchestration_service
from app.schemas.common import QueryRequest, StreamRequest
from app.schemas.orchestration import OrchestrationResponse
from app.services.orchestration_service import OrchestrationService
from app.utils.response_builder import ResponseBuilder
from app.utils.streaming import sse_event

router = APIRouter(prefix='/orchestration', tags=['orchestration'])


@router.post('/run', response_model=OrchestrationResponse)
def run(
    payload: QueryRequest,
    service: OrchestrationService = Depends(get_orchestration_service),
    _=Depends(get_current_user),
) -> OrchestrationResponse:
    result = service.run(query=payload.query, high_stakes=payload.high_stakes)
    return OrchestrationResponse(payload=result)


@router.post('/stream')
def stream(
    payload: StreamRequest,
    service: OrchestrationService = Depends(get_orchestration_service),
    _=Depends(get_current_user),
) -> StreamingResponse:
    def event_generator():
        try:
            yield from service.stream_run(query=payload.query, high_stakes=payload.high_stakes)
        except Exception as exc:  # pragma: no cover - handled at runtime
            yield sse_event('error', ResponseBuilder.success({'details': str(exc)}, message='stream_error'))

    return StreamingResponse(event_generator(), media_type='text/event-stream')
