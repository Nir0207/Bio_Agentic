import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.schemas.error import ErrorEnvelope

logger = get_logger('exceptions')


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _error_payload(code: str, message: str, request_id: str) -> dict[str, Any]:
    return ErrorEnvelope(error={'code': code, 'message': message, 'request_id': request_id}).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, 'request_id', '-')
        logger.error(
            'HTTP exception',
            extra={'route': str(request.url.path), 'error_details': {'status_code': exc.status_code, 'detail': exc.detail}},
        )
        detail = exc.detail if isinstance(exc.detail, str) else 'Request failed.'
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(code='http_error', message=detail, request_id=request_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, 'request_id', '-')
        logger.error(
            'Validation exception',
            extra={'route': str(request.url.path), 'error_details': {'errors': exc.errors()}},
        )
        return JSONResponse(
            status_code=422,
            content=_error_payload(code='validation_error', message='Request validation failed.', request_id=request_id),
        )

    @app.exception_handler(DomainError)
    async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
        request_id = getattr(request.state, 'request_id', '-')
        logger.error(
            'Domain exception',
            extra={'route': str(request.url.path), 'error_details': exc.details or exc.message},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(code=exc.code, message=exc.message, request_id=request_id),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, 'request_id', '-')
        logger.error(
            'Unhandled exception',
            extra={
                'route': str(request.url.path),
                'error_details': {'traceback': traceback.format_exc(), 'exception': str(exc)},
            },
        )
        return JSONResponse(
            status_code=500,
            content=_error_payload(code='internal_error', message='Internal server error.', request_id=request_id),
        )
