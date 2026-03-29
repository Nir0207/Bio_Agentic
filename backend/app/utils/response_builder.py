from typing import Any


class ResponseBuilder:
    @staticmethod
    def success(data: Any, message: str = 'ok') -> dict[str, Any]:
        return {'message': message, 'data': data}
