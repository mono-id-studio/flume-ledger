from typing import Any
from django.http import HttpRequest

from app.common.default.types import EndPointResponse
from app.middlewares.default.pipeline import NextPipe


def logger_mw(request: HttpRequest, data: Any, next: NextPipe) -> EndPointResponse:
    """
    Resolve a sequence of route handlers.
    """
    print("Log before request endpoint")
    response = next()
    print("Log after request endpoint")
    return response
