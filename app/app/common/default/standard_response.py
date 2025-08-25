from http import HTTPStatus
import json
from typing import Any, Generic, TypeVar
from app.common.default.utils import is_debug
from ninja import Schema
from ninja.responses import Response


# Define a generic type variable
T = TypeVar("T")


class StandardResponse(Schema, Generic[T]):
    """
    Represents a standard response object.

    Attributes:
        data (T or None): The data payload of the response.
        message (str): The message associated with the response.
    Methods:
        encode: Encodes the response object into bytes.
    """

    data: T | None
    message: str

    def encode(self) -> bytes:
        return json.dumps(self.dict()).encode()


class StandardErrorResponse(Schema):
    """
    Represents an error response.

    Attributes:
        dev (object or None): The developer-specific error details.
        code (int): The error code.
        desc (str): The error description.
    Methods:
        encode: Encodes the response object into bytes.
    """

    dev: Any | None
    code: int
    message: str

    def encode(self) -> bytes:
        return json.dumps(self.dict()).encode()


def standard_response(status_code: int | HTTPStatus, data: T, message: str) -> Response:
    """
    Create a standard response object.

    Args:
        status_code (int): The HTTP status code.
        data (Any): The data to be sent in the response.
        message (str): The message to be sent in the response.

    Returns:
        Response: The response object containing the data and message.

    """
    return Response(
        data=StandardResponse(data=data, message=message), status=status_code
    )


def standard_error(
    status_code: int | HTTPStatus, message: str, code: int, dev: str
) -> Response:
    """
    Create a standard error object.

    Args:
        status_code (int): The HTTP status code.
        message (str): The error message.
        code (int): The error code.
        stack_trace (str): The stack trace of the error.

    Returns:
        Response: The response object containing the error details.
    """
    development = dev if is_debug() else ""
    return Response(
        data=StandardErrorResponse(dev=development, code=code, message=message),
        status=status_code,
    )


def standard_list_response(
    status_code: int | HTTPStatus,
    data: list[T],
    message: str,
    page: int,
    total_pages: int,
) -> Response:
    """
    Create a standard response object.

    Args:
        status_code (int): The HTTP status code.
        data (Any): The data to be sent in the response.
        message (str): The message to be sent in the response.

    Returns:
        Response: The response object containing the data and message.

    """
    return Response(
        data=StandardListResponse(list=data, curr_page=page, total_pages=total_pages),
        status=status_code,
    )


class StandardListResponse(Schema, Generic[T]):
    list: list[T]
    curr_page: int
    total_pages: int
