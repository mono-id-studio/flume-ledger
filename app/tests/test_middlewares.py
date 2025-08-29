from json import dumps, loads
from unittest.mock import MagicMock, patch

import pytest
from app.common.default.globals import MICROSERVICE_INVALID_SIGNATURE
from app.common.default.test_utility import print_test_info, print_test_result
from app.middlewares.bootstrap_verification import bootstrap_verification
from app.schemas.req.services import RegisterRequest
from django.http import HttpRequest
from pydantic import AnyHttpUrl


@pytest.fixture
def mock_request() -> HttpRequest:
    request = HttpRequest()
    request.META["HTTP_AUTHORIZATION"] = "Bearer test-token"
    request.META["HTTP_X_TIMESTAMP"] = "1234567890"
    request.META["HTTP_X_NONCE"] = "test-nonce"
    request.META["HTTP_X_KEY_ID"] = "test-kid"
    request.META["HTTP_X_SIGNATURE"] = "test-signature"
    return request


@pytest.fixture
def register_request_data() -> RegisterRequest:
    return RegisterRequest(
        service_name="test-service",
        base_url=AnyHttpUrl("http://test.com"),
        bootstrap_secret_ref="test-secret-ref",
        boot_id="boot-id",
        node_id="node-id",
        task_slot=1,
        ttl_s=300,
        region="us-east-1",
        heartbeat_interval_sec=30,
        capabilities=None,
        meta=None,
        health_url=None,
    )


def test_bootstrap_verification_success(mock_request, register_request_data):
    print_test_info(
        "test_bootstrap_verification_success",
        "Test bootstrap verification success",
        {
            "request": mock_request,
            "register_request_data": register_request_data,
        },
        "OK",
    )
    next_middleware = MagicMock(return_value="OK")

    with patch(
        "app.middlewares.bootstrap_verification.SignerService"
    ) as mock_signer_service:
        mock_signer_instance = mock_signer_service.return_value
        mock_signer_instance.bootstrap_verification.return_value = (True, "")

        response = bootstrap_verification(
            mock_request, register_request_data, next_middleware
        )
        mock_signer_instance.bootstrap_verification.assert_called_once_with(
            token="test-token",
            ts=1234567890,
            nonce="test-nonce",
            kid="test-kid",
            signature="test-signature",
        )
        next_middleware.assert_called_once()
        assert response == "OK"
        print_test_result(
            "test_bootstrap_verification_success",
            "OK",
            response,
        )


def test_bootstrap_verification_failure(mock_request, register_request_data):
    next_middleware = MagicMock()

    with patch(
        "app.middlewares.bootstrap_verification.SignerService"
    ) as mock_signer_service:
        mock_signer_instance = mock_signer_service.return_value
        mock_signer_instance.bootstrap_verification.return_value = (
            False,
            "Invalid signature",
        )

        response = bootstrap_verification(
            mock_request, register_request_data, next_middleware
        )
        mock_signer_instance.bootstrap_verification.assert_called_once()
        next_middleware.assert_not_called()
        assert response.status_code == 401
        content = loads(response.content)
        assert content["code"] == MICROSERVICE_INVALID_SIGNATURE
        assert content["message"] == "Invalid signature"


def test_bootstrap_verification_missing_header(register_request_data):
    next_middleware = MagicMock()

    request = HttpRequest()
    request.headers = {
        "X-Timestamp": "1234567890",
        "X-Nonce": "test-nonce",
        "X-Signature": "test-signature",
    }
    with pytest.raises(KeyError):
        bootstrap_verification(request, register_request_data, next_middleware)


def test_bootstrap_verification_malformed_auth_header(register_request_data):
    next_middleware = MagicMock()

    request = HttpRequest()
    request.headers = {
        "Authorization": "WrongFormat",
        "X-Timestamp": "1234567890",
        "X-Nonce": "test-nonce",
        "X-Signature": "test-signature",
    }

    with pytest.raises(IndexError):
        bootstrap_verification(request, register_request_data, next_middleware)
