from django.http import HttpResponse

from app.common.default.standard_response import standard_error
from app.common.default.utils import c_debug


def exception_handler(request, exc, status_code=500):
    """
    This function is used to handle exceptions in the API.

    :param request: HttpRequest
    :param exc: Exception
    :param status_code: int
    :return: HttpResponse
    """
    c_debug(exc)
    return HttpResponse(
        content=standard_error(
            status_code=status_code,
            message="",
            code=status_code,
            dev=exc.errors if hasattr(exc, "errors") else str(exc),
        ),
        status=status_code,
        content_type="application/json",
    )
