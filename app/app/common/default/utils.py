import os
from typing import Any, Dict, Tuple, TypeVar
from django.http import HttpRequest
from django.db.models.fields import Field
from django.db.models.query import QuerySet as ValueQuerySet
from django.core.paginator import Paginator, EmptyPage, Page
from datetime import date, datetime, time
from urllib.parse import quote, unquote
from app.models.default.base_model import BaseModel


def is_debug() -> bool:
    """
    Check if the application is running in debug mode.

    Returns:
        bool: True if the application is running in debug mode, False otherwise.
    """
    return os.getenv("DEBUG") == "True"


def c_info(message: str):
    """
    Print an informational message.

    Args:
        message (str): The message to be printed.
    """
    print(f"[INFO] {message}")


def c_debug(message: str):
    """
    Print a debug message.

    Args:
        message (str): The message to be printed.
    """
    if is_debug():
        print(f"[DEBUG] {message}")


def c_error(message: str):
    """
    Print an error message.

    Args:
        message (str): The message to be printed.
    """
    print(f"[ERROR] {message}")


def c_warning(message: str):
    """
    Print a warning message.

    Args:
        message (str): The message to be printed.
    """
    print(f"[WARNING] {message}")


def c_success(message: str):
    """
    Print a success message.

    Args:
        message (str): The message to be printed.
    """
    print(f"[SUCCESS] {message}")


def get_route_param(request: HttpRequest, param_name: str) -> str | None:
    """
    Get a parameter from a request.

    Args:
        request (HttpRequest): The request object.
        param_name (str): The name of the parameter.

    Returns:
        str: The value of the parameter, or an empty string if the parameter is not found.
    """
    response = (
        request.resolver_match.kwargs.get(param_name, "")
        if request.resolver_match is not None
        else ""
    )
    return str(response) if response is not None else ""


T = TypeVar("T", str, int, float, bool, date, time, datetime)


def get_query_param(request: HttpRequest, param_name: str, default: T) -> T:
    """
    Get a query parameter from a request.

    Args:
        request (HttpRequest): The request object.
        param_name (str): The name of the query parameter.

    Returns:
        str: The value of the query parameter, or an empty string if the parameter is not found.
    """
    if isinstance(default, str):
        return str(request.GET.get(param_name, default))

    if isinstance(default, bool):
        return bool(request.GET.get(param_name, default))

    if isinstance(default, int):
        return int(request.GET.get(param_name, default))

    if isinstance(default, float):
        return float(request.GET.get(param_name, default))

    if isinstance(default, datetime):
        return datetime.fromisoformat(request.GET.get(param_name, default.isoformat()))

    if isinstance(default, time):
        return time.fromisoformat(request.GET.get(param_name, default.isoformat()))

    if isinstance(default, date):
        return date.fromisoformat(request.GET.get(param_name, default.isoformat()))

    return default


def append_data_to_req(request: HttpRequest, data: object) -> HttpRequest:
    """
    Append data to the request object.

    Args:
        request (HttpRequest): The request object.
        data (object): The data to be appended.

    Returns:
        HttpRequest: The updated request object.
    """
    setattr(request, "appended_data", data)
    return request


T1 = TypeVar("T1")


def get_data_from_req(request: HttpRequest) -> Any:
    """
    Get appended data from the request object.

    Args:
        request (HttpRequest): The request object.

    Returns:
        Optional[T]: The appended data or None if not present.
    """
    return getattr(request, "appended_data")


SUBMODEL = TypeVar("SUBMODEL", bound=BaseModel)


def order_query_set(
    query_set: ValueQuerySet[SUBMODEL], order_by: str
) -> ValueQuerySet[SUBMODEL]:
    """
    Order a query set by a given field.

    Args:
        query_set (QuerySet): The query set to be ordered.
        order_by (str): The field to order by.

    Returns:
        QuerySet: The ordered query set.
    """
    field_to_order = order_by.split(",") if "," in order_by else [order_by]
    valid_order_fields = [f.name for f in query_set.model._meta.get_fields()]
    safe_order_fields = [
        field for field in field_to_order if field.lstrip("-") in valid_order_fields
    ]
    result = query_set
    if safe_order_fields:
        result = query_set.order_by(*safe_order_fields)
    return result


def select_query_set(
    query_set: ValueQuerySet[SUBMODEL, Any], select: str
) -> ValueQuerySet[SUBMODEL, Dict[str, Any]]:
    """
    Select fields from a query set.

    Args:
        query_set (QuerySet): The query set to be selected.
        select (str): The fields to select.

    Returns:
        QuerySet: The selected query set.
    """
    select_fields = select.split(",") if "," in select else [select]
    result = query_set
    if select_fields:
        # Validate fields to prevent SQL injection
        valid_fields = [
            f.name for f in query_set.model._meta.get_fields() if isinstance(f, Field)
        ]
        safe_select_fields = [field for field in select_fields if field in valid_fields]
        if safe_select_fields:
            result = query_set.values(*safe_select_fields)
    return result


def paginate_query_set(
    query_set: ValueQuerySet[SUBMODEL, SUBMODEL], page: int, per_page: int
) -> Tuple[Page[SUBMODEL], int]:
    """
    Paginate a query set.

    Args:
        query_set (QuerySet): The query set to be paginated.
        page (int): The current page.
        per_page (int): The number of items per page.

    Returns:
        QuerySet: The paginated query set.
    """
    paginator = Paginator(query_set, per_page)
    try:
        subset = paginator.page(page)
    except EmptyPage:
        subset = paginator.page(paginator.num_pages)
    return subset, paginator.num_pages


def encode_argument(argument: str, safe: str = "/") -> str:
    """
    Encode an argument.
    """
    return quote(argument, safe=safe)


def decode_argument(argument: str, encoding: str = "utf-8") -> str:
    """
    Decode an argument.
    """
    return unquote(argument, encoding=encoding)


def get_image_format_from_extension(file_extension):
    """
    Get the image format from the file extension

    Args:
        file_extension: str - the file extension without the dot
    """
    # Dictionary mapping file extensions to image formats
    image_formats = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "bmp": "BMP",
        "gif": "GIF",
        "tiff": "TIFF",
        "webp": "WEBP",
        "heif": "HEIF",
        # You can easily add more formats as required
    }

    # Convert the file extension to lowercase for uniformity
    return image_formats.get(file_extension.lower(), "Unknown format")


def set_if_diff(obj: Any, field: str, value: Any) -> bool:
    """
    Set a field on an object if the value is different from the current value.
    """
    if getattr(obj, field) != value:
        setattr(obj, field, value)
        return True
    return False
