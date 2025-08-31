from typing import Any
import pytest
from django.http import HttpRequest
from types import SimpleNamespace
from datetime import datetime, time
from app.common.default import utils
from app.models.services import Service


def test_is_debug(monkeypatch):
    """
    Tests the is_debug utility by mocking the DEBUG environment variable.
    """
    monkeypatch.setenv("DEBUG", "True")
    assert utils.is_debug() is True
    monkeypatch.setenv("DEBUG", "False")
    assert utils.is_debug() is False
    monkeypatch.delenv("DEBUG")
    assert utils.is_debug() is False


def test_console_output(capsys):
    """
    Tests the console output functions (c_info, c_debug, etc.)
    by capturing stdout.
    """
    utils.c_info("Info message")
    captured = capsys.readouterr()
    assert "[INFO] Info message" in captured.out

    utils.c_error("Error message")
    captured = capsys.readouterr()
    assert "[ERROR] Error message" in captured.out

    utils.c_warning("Warning message")
    captured = capsys.readouterr()
    assert "[WARNING] Warning message" in captured.out

    utils.c_success("Success message")
    captured = capsys.readouterr()
    assert "[SUCCESS] Success message" in captured.out


def test_c_debug_output(capsys, monkeypatch):
    """
    Tests that c_debug only prints when DEBUG is enabled.
    """
    monkeypatch.setenv("DEBUG", "True")
    utils.c_debug("Debug message")
    captured = capsys.readouterr()
    assert "[DEBUG] Debug message" in captured.out

    monkeypatch.setenv("DEBUG", "False")
    utils.c_debug("Another debug message")
    captured = capsys.readouterr()
    assert "Another debug message" not in captured.out


def test_get_route_param(rf):
    request = rf.get("/qualunque/route/")
    # mock di resolver_match con la sola cosa che ci serve: kwargs
    request.resolver_match = SimpleNamespace(kwargs={"my_param": "123"})

    assert utils.get_route_param(request, "my_param") == "123"
    assert utils.get_route_param(request, "non_existent") == ""


def test_get_query_param(rf):
    """
    Tests retrieval of various types of query parameters.
    """
    request_str = rf.get("/path?name=test")
    assert utils.get_query_param(request_str, "name", "default") == "test"

    request_int = rf.get("/path?value=123")
    assert utils.get_query_param(request_int, "value", 0) == 123

    request_bool = rf.get("/path?flag=true")
    assert utils.get_query_param(request_bool, "flag", False) is True

    request_float = rf.get("/path?num=1.23")
    assert utils.get_query_param(request_float, "num", 0.0) == 1.23

    dt_str = "2023-01-01T12:00:00"
    request_dt = rf.get(f"/path?timestamp={dt_str}")
    assert utils.get_query_param(
        request_dt, "timestamp", datetime.now()
    ) == datetime.fromisoformat(dt_str)

    time_str = "12:00:00"
    request_time = rf.get(f"/path?time={time_str}")
    assert utils.get_query_param(
        request_time, "time", datetime.now().time()
    ) == time.fromisoformat(time_str)

    date_str = "2023-01-01"
    request_date = rf.get(f"/path?date={date_str}")
    assert (
        utils.get_query_param(request_date, "date", datetime.now().date())
        == datetime.fromisoformat(date_str).date()
    )

    obj = b"123"
    request_obj = rf.get(f"/path?obj={obj}")
    assert utils.get_query_param(request_obj, "obj", obj) == obj


def test_append_and_get_data_from_req():
    """
    Tests appending data to and retrieving data from a request object.
    """
    request = HttpRequest()
    data_to_append = {"key": "value"}
    updated_request = utils.append_data_to_req(request, data_to_append)
    retrieved_data = utils.get_data_from_req(updated_request)
    assert retrieved_data == data_to_append


@pytest.mark.django_db
def test_order_query_set(service_factory):
    """
    Tests ordering of a QuerySet.
    """
    s1 = service_factory(name="alpha-service")
    s2 = service_factory(name="beta-service")
    qs = Service.objects.all()

    ordered_qs = utils.order_query_set(qs, "name")
    assert list(ordered_qs) == [s1, s2]

    ordered_qs_desc = utils.order_query_set(qs, "-name")
    assert list(ordered_qs_desc) == [s2, s1]


@pytest.mark.django_db
def test_select_query_set(service_factory):
    """
    Tests selecting specific fields from a QuerySet.
    """
    service = service_factory(name="my-service")
    qs = Service.objects.all()
    selected_qs = utils.select_query_set(qs, "name")
    assert len(selected_qs) == 1
    assert selected_qs[0] == {"name": "my-service"}


@pytest.mark.django_db
def test_paginate_query_set(service_factory):
    """
    Tests pagination of a QuerySet.
    """
    for i in range(10):
        service_factory(name=f"service-{i}")

    qs = Service.objects.order_by("name")
    page_obj, num_pages = utils.paginate_query_set(qs, page=2, per_page=3)

    assert num_pages == 4
    assert len(page_obj.object_list) == 3
    assert page_obj.object_list[0].name == "service-3"


def test_encode_decode_argument():
    """
    Tests URL encoding and decoding of arguments.
    """
    original = "a test string with spaces/"
    encoded = utils.encode_argument(original, safe="&")
    assert encoded == "a%20test%20string%20with%20spaces%2F"
    decoded = utils.decode_argument(encoded)
    assert decoded == original

    original = "a test string with spaces/"
    encoded = utils.encode_argument(original, safe="/")
    assert encoded == "a%20test%20string%20with%20spaces/"
    decoded = utils.decode_argument(encoded)
    assert decoded == original


def test_get_image_format_from_extension():
    """
    Tests mapping of file extensions to image formats.
    """
    assert utils.get_image_format_from_extension("jpg") == "JPEG"
    assert utils.get_image_format_from_extension("PNG") == "PNG"
    assert utils.get_image_format_from_extension("unknown") == "Unknown format"


def test_set_if_diff():
    """
    Tests the set_if_diff utility to conditionally set an attribute.
    """
    obj = SimpleNamespace(field="initial_value")

    # Value is different, should be set and return True
    changed = utils.set_if_diff(obj, "field", "new_value")
    assert changed is True
    assert obj.field == "new_value"

    # Value is the same, should not be set and return False
    changed_again = utils.set_if_diff(obj, "field", "new_value")
    assert changed_again is False
    assert obj.field == "new_value"
