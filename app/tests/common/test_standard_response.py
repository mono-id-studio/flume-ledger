from json import dumps
from unittest import mock
import os
from app.common.default.standard_response import (
    StandardErrorResponse,
    StandardResponse,
    standard_response,
    standard_error,
    standard_list_response,
)


def test_standard_response():
    response = StandardResponse(data="test", message="test")
    assert response.dict() == {"data": "test", "message": "test"}

    assert response.encode() == b'{"data": "test", "message": "test"}'
    assert response.data == "test"
    assert response.message == "test"


def test_standard_error():
    response = StandardErrorResponse(dev="test", code=500, message="test")
    assert response.dict() == {"dev": "test", "code": 500, "message": "test"}
    assert response.encode() == dumps(response.dict()).encode()
    assert response.dev == "test"
    assert response.code == 500
    assert response.message == "test"


def test_standard_response_function():
    response = standard_response(status_code=200, data="test", message="test")
    assert response.status_code == 200
    assert response.content == b'{"data": "test", "message": "test"}'


def test_standard_error_function():
    with mock.patch.dict(os.environ, {"DEBUG": "False"}):
        response = standard_error(status_code=500, code=500, dev="test", message="test")
        assert response.status_code == 500
        assert response.content == b'{"dev": "", "message": "test", "code": 500}'

    with mock.patch.dict(os.environ, {"DEBUG": "True"}):
        response = standard_error(status_code=500, code=500, dev="test", message="test")
        assert response.status_code == 500
        assert response.content == b'{"dev": "test", "message": "test", "code": 500}'


def test_standard_list_response_function():
    response = standard_list_response(
        status_code=200, data=[1, 2, 3], message="test", page=1, total_pages=1
    )
    assert response.status_code == 200
    assert response.content == b'{"list": [1, 2, 3], "curr_page": 1, "total_pages": 1}'
