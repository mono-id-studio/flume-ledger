import json
from unittest.mock import patch, MagicMock
import pytest
import django.db.utils
from app.services.secrets import SecretsService, SecretObject
from app.common.default.security import token_to_bytes


@pytest.fixture(autouse=True)
def clear_secrets_cache():
    """
    Fixture to automatically clear the SecretsService cache before each test.
    This ensures test isolation.
    """
    SecretsService.cache.clear()


@pytest.fixture
def mock_boto_client():
    """
    Fixture to mock the boto3 client and the secretsmanager interface.
    """
    with patch("app.services.secrets.client") as mock_client:
        mock_sm = MagicMock()
        mock_client.return_value = mock_sm
        yield mock_sm


def setup_secret(mock_sm, secret_data):
    """
    Helper function to set the return value of get_secret_value.
    """
    mock_sm.get_secret_value.return_value = {"SecretString": json.dumps(secret_data)}


@pytest.mark.django_db
def test_get_fetches_from_aws_and_caches(service_factory, mock_boto_client):
    """
    Tests that SecretsService.get fetches a secret from AWS on the first call
    and uses the cache for subsequent calls.
    """
    secret_ref = "my-secret"
    secret_data = {
        "token": "dG9rZW4=",  # "token" in base64
        "kid": "v1",
        "prev_token": "cHJldl90b2tlbg==",  # "prev_token" in base64
        "prev_kid": "v0",
    }
    setup_secret(mock_boto_client, secret_data)
    service = service_factory(bootstrap_secret_ref=secret_ref, region="eu-central-1")

    # First call should fetch from AWS
    secret_obj = SecretsService.get(service, region=service.region)

    assert isinstance(secret_obj, SecretObject)
    assert secret_obj.token == secret_data["token"]
    assert secret_ref in SecretsService.cache
    mock_boto_client.get_secret_value.assert_called_once_with(SecretId=secret_ref)

    # Second call should use the cache
    SecretsService.get(service)
    mock_boto_client.get_secret_value.assert_called_once()  # Not called again


@pytest.mark.django_db
def test_get_current(service_factory, mock_boto_client):
    """
    Tests that get_current returns the correct kid and token bytes.
    """
    secret_data = {"token": "dG9rZW4=", "kid": "v1"}
    setup_secret(mock_boto_client, secret_data)
    service = service_factory()

    current_secret = SecretsService.get_current(service)

    assert current_secret is not None
    kid, token_bytes = current_secret
    assert kid == "v1"
    assert token_bytes == token_to_bytes(secret_data["token"])


@pytest.mark.django_db
def test_get_current_no_secret(service_factory):
    """
    Tests that get_current returns None when the service has no secret.
    """
    # must raise an error to pass the test
    with pytest.raises(django.db.utils.IntegrityError):
        service_factory(bootstrap_secret_ref=None)


@pytest.mark.django_db
def test_get_previous(service_factory, mock_boto_client):
    """
    Tests that get_previous returns the correct previous kid and token bytes.
    """
    secret_data = {
        "token": "dG9rZW4=",
        "kid": "v1",
        "prev_token": "cHJldl90b2tlbg==",
        "prev_kid": "v0",
    }
    setup_secret(mock_boto_client, secret_data)
    service = service_factory()

    previous_secret = SecretsService.get_previous(service)

    assert previous_secret is not None
    kid, token_bytes = previous_secret
    assert kid == "v0"
    assert token_bytes == token_to_bytes(secret_data["prev_token"])


@pytest.mark.django_db
def test_get_previous_not_available(service_factory, mock_boto_client):
    """
    Tests that get_previous returns None when the secret does not contain a previous token.
    """
    secret_data = {"token": "dG9rZW4=", "kid": "v1"}  # No prev_token/kid
    setup_secret(mock_boto_client, secret_data)
    service = service_factory()

    assert SecretsService.get_previous(service) is None
