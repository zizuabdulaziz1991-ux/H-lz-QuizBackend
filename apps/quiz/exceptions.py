from rest_framework.exceptions import APIException, Throttled
from rest_framework.views import exception_handler


class QuizError(APIException):
    def __init__(self, code, message, status_code=400):
        self.status_code = status_code
        self.code = code
        super().__init__(message, code)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    if isinstance(exc, QuizError):
        code = exc.code
    elif isinstance(exc, Throttled):
        code = "rate_limited"
    else:
        code = getattr(exc, "default_code", "error")
    message = exc.detail if isinstance(exc.detail, str) else str(response.data)
    response.data = {"error": {"code": code, "message": message}}
    return response
