from typing import Callable, Optional, TypeAlias, TypeVar
from django.http import HttpRequest
from ninja.responses import Response

EndPointResponse: TypeAlias = Response
"""
Represents the response from an endpoint.

It's a tuple containing:
1. An HTTP status code (either as HTTPStatus enum or int)
2. Either a StandardResponse or StandardErrorResponse object

This type allows for both successful and error responses.
"""

T = TypeVar("T")
EndPoint: TypeAlias = Callable[[HttpRequest, Optional[T]], EndPointResponse]
"""
Represents an endpoint function.

This type alias defines a callable (function) that:
- Takes a single parameter of type HttpRequest
- Returns an EndPointResponse

Typical usage:
def my_endpoint(request: HttpRequest) -> EndPointResponse:
    # Endpoint logic here
    ...
"""
