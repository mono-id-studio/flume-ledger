from typing import Annotated, Any, Dict, Type, TypeAlias, TypeVar

from ninja import Field

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
# --- 400 ---


class BadRequestResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=400)
    ] = 400
    message: Annotated[
        str,
        Field(description="The error message", title="Message", example="Bad Request"),
    ] = "Bad Request"


# --- 401 ---


class UnauthorizedResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=401)
    ] = 401
    message: Annotated[
        str,
        Field(description="The error message", title="Message", example="Unauthorized"),
    ] = "Unauthorized"


# --- 403 ---


class ForbiddenResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=403)
    ] = 403
    message: Annotated[
        str,
        Field(description="The error message", title="Message", example="Forbidden"),
    ] = "Forbidden"


# --- 404 ---


class NotFoundResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=404)
    ] = 404
    message: Annotated[
        str,
        Field(description="The error message", title="Message", example="Not Found"),
    ] = "Not Found"


# --- 405 ---


class MethodNotAllowedResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=405)
    ] = 405
    message: Annotated[
        str,
        Field(
            description="The error message",
            title="Message",
            example="Method Not Allowed",
        ),
    ] = "Method Not Allowed"


# --- 409 ---


class ConflictResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=409)
    ] = 409
    message: Annotated[
        str, Field(description="The error message", title="Message", example="Conflict")
    ] = "Conflict"


# --- 422 ---


class UnprocessableEntityResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=422)
    ] = 422
    message: Annotated[
        str,
        Field(
            description="The error message",
            title="Message",
            example="Unprocessable Entity",
        ),
    ] = "Unprocessable Entity"


# --- 500 ---


class InternalServerErrorResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=500)
    ] = 500
    message: Annotated[
        str,
        Field(
            description="The error message",
            title="Message",
            example="Internal Server Error",
        ),
    ] = "Internal Server Error"


# --- 501 ---


class NotImplementedResponse(StandardErrorResponse):
    code: Annotated[
        int, Field(description="The error code", title="Code", example=501)
    ] = 501
    message: Annotated[
        str,
        Field(
            description="The error message", title="Message", example="Not Implemented"
        ),
    ] = "Not Implemented"


ErrorResponseStates: ResponseType = {
    # ---  Error responses 4XX
    400: BadRequestResponse,
    401: UnauthorizedResponse,
    403: ForbiddenResponse,
    404: NotFoundResponse,
    405: MethodNotAllowedResponse,
    409: ConflictResponse,
    422: UnprocessableEntityResponse,
    # ---  Server responses 5XX
    500: InternalServerErrorResponse,
    501: NotImplementedResponse,
}
"""
A dictionary that maps HTTP status codes to response types.
"""


def responses(
    to_add: Dict[
        int,
        Type[StandardResponse[Any] | StandardListResponse[Any]]
        | Type[StandardErrorResponse]
        | None,
    ],
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
        int,
        Type[StandardResponse[Any] | StandardListResponse[Any]]
        | Type[StandardErrorResponse]
        | None,
    ] = {
        200: StandardResponse[Any],
        204: None,
    }
    return responses(to_add)
