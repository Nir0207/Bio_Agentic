import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

REQUEST_ID_CTX: ContextVar[str] = ContextVar('request_id', default='-')


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'request_id': REQUEST_ID_CTX.get(),
            'route': getattr(record, 'route', '-'),
            'service': getattr(record, 'service', record.name),
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['error'] = self.formatException(record.exc_info)
        if hasattr(record, 'error_details'):
            payload['error_details'] = getattr(record, 'error_details')
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str = 'INFO') -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.handlers = [handler]


def get_logger(service: str) -> logging.LoggerAdapter:
    logger = logging.getLogger(service)
    return logging.LoggerAdapter(logger, {'service': service})
