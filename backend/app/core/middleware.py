import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import REQUEST_ID_CTX, get_logger

logger = get_logger('http')


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        token = REQUEST_ID_CTX.set(request_id)
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        finally:
            REQUEST_ID_CTX.reset(token)

        response.headers['X-Request-ID'] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            'Request completed',
            extra={
                'route': request.url.path,
                'error_details': {
                    'method': request.method,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                },
            },
        )
        return response
