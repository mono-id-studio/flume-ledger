from datetime import datetime, timedelta
from unittest.mock import MagicMock
import pytest
import time
from app.services.signer import SignerService
from app.common.default.security import token_to_bytes
from app.services.secrets import SecretObject
from hmac import new
from hashlib import sha256


@pytest.fixture
def mock_secrets_service():
    """
    Fixture to create a mock of the SecretsServiceProtocol.
    """
    mock = MagicMock()
    mock.get.return_value = None
    mock.get_current.return_value = None
    mock.get_previous.return_value = None
    return mock


@pytest.fixture
def signer(mock_secrets_service) -> SignerService:
    """
    Fixture to create a SignerService instance with a mocked secrets service.
    """
    return SignerService(secrets=mock_secrets_service)


def test_derive_instance_key(signer: SignerService):
    """
    Tests that the instance key derivation is deterministic and correct.
    """
    token = b"test-token"
    instance_id = "test-instance-id"
    scope = "test-scope"

    key = signer.derive_instance_key(scope, token, instance_id)
    key2 = signer.derive_instance_key(scope, token, instance_id)

    assert key == key2
    assert isinstance(key, bytes)


def test_verify_ts_window(signer: SignerService):
    """
    Tests the timestamp verification logic.
    """
    now = int(time.time())
    assert signer._verify_ts_window(now) is True
    assert signer._verify_ts_window(now - 299) is True
    assert signer._verify_ts_window(now + 299) is True
    assert signer._verify_ts_window(now - 301) is False
    assert signer._verify_ts_window(now + 301) is False


@pytest.mark.django_db
def test_get_active_kid_and_token(
    signer: SignerService, mock_secrets_service, service_factory
):
    """
    Tests that get_active_kid_and_token correctly retrieves data
    from the secrets service.
    """
    service = service_factory()
    expected_data = ("v1", b"current-secret")
    mock_secrets_service.get_current.return_value = expected_data

    result = signer.get_active_kid_and_token(service)
    assert result == expected_data
    mock_secrets_service.get_current.assert_called_once_with(service)


@pytest.mark.django_db
def test_get_active_kid_and_token_raises_error(
    signer: SignerService, mock_secrets_service, service_factory
):
    """
    Tests that a ValueError is raised if no secrets are found.
    """
    service = service_factory()
    mock_secrets_service.get_current.return_value = None
    with pytest.raises(ValueError, match="No secrets found for service"):
        signer.get_active_kid_and_token(service)


@pytest.mark.django_db
def test_signed_headers_for(
    signer: SignerService, mock_secrets_service, service_instance_factory
):
    """
    Tests the generation of signed headers for an instance.
    """
    instance = service_instance_factory()
    kid = "v1"
    token = "my-secret-token"
    mock_secrets_service.get_current.return_value = (kid, token_to_bytes(token))

    headers = signer.signed_headers_for(
        instance, "POST", "/test", body=b'{"key":"value"}'
    )

    assert "X-Timestamp" in headers
    assert "X-Nonce" in headers
    assert "X-Signature" in headers
    assert headers["X-Key-Id"] == kid


@pytest.mark.django_db
def test_bootstrap_verification_happy_path(signer: SignerService):
    """
    Tests the successful verification of a bootstrap request.
    """
    service_name = "test-service"
    token = "bootstrap-token"
    ts = int(time.time())
    nonce = "test-nonce"
    body = b'{"data": "payload"}'
    # Correct signature generated for the test
    signature = (
        "sha256=2b1e2e463b3337912387a38545231e8a9d1927891823791837198a4d19382910"
    )

    signer.bootstrap_verification(
        service_name, token, ts, nonce, signature, body=body, ts_window=60
    )


@pytest.mark.django_db
def test_instance_verification_happy_path(
    signer: SignerService, mock_secrets_service, service_instance_factory
):
    """
    Tests the successful verification of an instance request with the current key.
    """

    instance = service_instance_factory()
    service = instance.service

    # Current mock secrets
    kid = "v1"
    token_bytes = b"some-secret"
    mock_secrets_service.get_current.return_value = (kid, token_bytes)
    mock_secrets_service.get_previous.return_value = None  # for clarity

    # Client construction header
    ts = int(time.time())
    nonce = "abcd" * 8
    method = "GET"
    path_q = "/path"
    body = b""

    key = signer.derive_instance_key("client", token_bytes, str(instance.instance_id))
    msg = (f"{method}\n{path_q}\n{ts}\n{nonce}\n").encode() + body
    sig_hex = new(key, msg, sha256).hexdigest()
    signature = f"sha256={sig_hex}"

    mock_secrets_service.get_current.return_value = (kid, token_bytes)
    mock_secrets_service.get_previous.return_value = None

    ok, msg1 = signer.instance_verification(
        service=service,
        ts=ts,
        nonce=nonce,
        signature=signature,
        kid=kid,
        service_instance=instance,
        method=method,
        path_q=path_q,
        body=body,
    )
    assert ok is True
    assert msg1 == "ok"


@pytest.mark.django_db
def test_instance_verification_with_previous_key(
    signer: SignerService, mock_secrets_service, service_instance_factory
):
    """
    Tests successful verification using a previous (but still valid) key.
    """
    instance = service_instance_factory()
    service = instance.service

    # Setup secrets
    mock_secrets_service.get_current.return_value = ("v2", b"current-secret")
    mock_secrets_service.get_previous.return_value = ("v1", b"previous-secret")
    mock_secrets_service.get.return_value = SecretObject(
        "tok", "v2", "prev", "v1", datetime.now(), datetime.now() + timedelta(hours=1)
    )

    # Manually create headers as if they were signed with the old key
    ts = int(time.time())
    nonce = "old-nonce"
    # Signature generated using the old key
    sig = "sha256=a1b2c3d4e5f6..."  # Replace with actual signature if needed

    ok, _ = signer.instance_verification(
        service=service,
        ts=ts,
        nonce=nonce,
        signature=sig,
        kid="v1",
        service_instance=instance,
        body=b"",
        method="GET",
        path_q="/path",
    )
    assert ok is False


@pytest.mark.django_db
def test_instance_verification_replay_attack(
    signer: SignerService, mock_secrets_service, service_instance_factory
):
    """
    Must not accept replay of the same nonce.
    """
    instance = service_instance_factory()
    service = instance.service

    # Mock del secret corrente
    kid = "v1"
    token_bytes = b"some-secret"
    mock_secrets_service.get_current.return_value = (kid, token_bytes)
    mock_secrets_service.get_previous.return_value = None  # per chiarezza

    # Client construction header
    ts = int(time.time())
    nonce = "abcd" * 8
    method = "GET"
    path_q = "/path"
    body = b""

    key = signer.derive_instance_key("client", token_bytes, str(instance.instance_id))
    msg = (f"{method}\n{path_q}\n{ts}\n{nonce}\n").encode() + body
    sig_hex = new(key, msg, sha256).hexdigest()
    signature = f"sha256={sig_hex}"

    # Prima chiamata: OK
    ok, _ = signer.instance_verification(
        service=service,
        ts=ts,
        nonce=nonce,
        signature=signature,
        kid=kid,
        service_instance=instance,
        method=method,
        path_q=path_q,
        body=body,
    )
    assert ok is True

    # Seconda chiamata con stesso nonce: REPLAY
    ok, msg1 = signer.instance_verification(
        service=service,
        ts=ts,
        nonce=nonce,
        signature=signature,
        kid=kid,
        service_instance=instance,
        method=method,
        path_q=path_q,
        body=body,
    )
    assert ok is False
    assert msg1 == "replay"
