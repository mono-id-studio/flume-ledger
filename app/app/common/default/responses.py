from typing import Any, Dict, Type, TypeAlias, TypeVar

from app.common.default.standard_response import (
    StandardErrorResponse,
    StandardListResponse,
    StandardResponse,
)

# Define a generic type variable
T = TypeVar("T")

ResponseType: TypeAlias = dict[
    int,
    Type[StandardErrorResponse | StandardResponse[Any] | StandardListResponse[Any]]
    | None,
]
"""
Represents a dictionary that maps HTTP status codes to response types.
"""


ErrorResponseStates: ResponseType = {
    # ---  Error responses 4XX
    400: StandardErrorResponse,
    401: StandardErrorResponse,
    403: StandardErrorResponse,
    404: StandardErrorResponse,
    405: StandardErrorResponse,
    409: StandardErrorResponse,
    422: StandardErrorResponse,
    # ---  Server responses 5XX
    500: StandardErrorResponse,
    501: StandardErrorResponse,
}
"""
A dictionary that maps HTTP status codes to response types.
"""


def responses(
    to_add: Dict[int, Type[StandardResponse[Any] | StandardListResponse[Any]] | None],
) -> ResponseType:
    """
    Adds the given response types to the existing dictionary of responses.

    Args:
        to_add (dict[int, Type[StandardResponse[Any]]]): The response types to add.
    """
    temp = ErrorResponseStates.copy()
    for k, v in to_add.items():
        temp[k] = v
    return temp


def default_responses() -> ResponseType:
    """
    Returns the default dictionary of responses, extended with a 200 status code
    mapped to a StandardResponse of type T.

    Args:
        custom_type (Type[T]): The type of the data expected in the successful response.

    Returns:
        ResponseType: The updated dictionary with a successful response type added.
    """
    to_add: Dict[
        int, Type[StandardResponse[Any] | StandardListResponse[Any]] | None
    ] = {
        200: StandardResponse[Any],
        204: None,
    }
    return responses(to_add)
