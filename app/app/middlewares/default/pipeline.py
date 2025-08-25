import inspect
from typing import Any, Callable, Sequence, TypeAlias, Union

from django.http import HttpRequest

from app.common.default.types import EndPointResponse

# Types for endpoint callables handled by the pipeline
EndpointCallableWithData = Callable[[HttpRequest, Any], EndPointResponse]
EndpointCallableWithoutData = Callable[[HttpRequest], EndPointResponse]
FlexibleEndpointType = Union[EndpointCallableWithData, EndpointCallableWithoutData]


NextPipe: TypeAlias = Callable[[], EndPointResponse]
"""
Represents the next pipe in a route pipeline.
"""
RoutePipe: TypeAlias = Callable[[HttpRequest, Any, NextPipe], EndPointResponse]
"""
Represents a route handler function.
"""


def pipeline(
    request: HttpRequest,
    *handlers: RoutePipe,
    endpoint: FlexibleEndpointType,
    data: Any | None = None,
) -> EndPointResponse:
    """
    Resolve a sequence of route handlers.

    Args:
        *handlers (RoutePipe): A sequence of route handlers.
        endpoint (FlexibleEndpointType): The final endpoint to call.
        data (Optional[T]): Optional data to pass to handlers and the endpoint.

    Returns:
        EndPointResponse: The response from the resolved route handlers.
    """
    response = execute_pipeline(handlers, 0, request, endpoint, data)
    return response


def execute_pipeline(
    pipeline_sequence: Sequence[RoutePipe],
    index: int,
    request: HttpRequest,
    endpoint: Union[
        Callable[[HttpRequest, Any], EndPointResponse],
        Callable[[HttpRequest], EndPointResponse],
    ],
    data: Any,
) -> EndPointResponse:
    """
    Execute a route pipeline.
    """
    current_func = pipeline_sequence[index] if index < len(pipeline_sequence) else None

    def next_func():
        return execute_pipeline(pipeline_sequence, index + 1, request, endpoint, data)

    if current_func is None:
        # Inspect the endpoint signature to call it correctly
        sig = inspect.signature(endpoint)
        num_params = len(sig.parameters)

        # Assuming param 1 is always 'request'. If more params, pass 'data'.
        # A more robust check could be by parameter names like 'data' if standardized.
        if num_params > 1:
            # We've checked it takes more than one param, assume it's (request, data)
            return endpoint(request, data)  # type: ignore[call-arg]
        else:
            # We've checked it takes one param, assume it's (request)
            return endpoint(request)  # type: ignore[call-arg]
    # The T for RoutePipe's data argument is passed along.
    return current_func(request, data, next_func)
