import pytest
from django.test import RequestFactory
from app.models.services import Service


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def service_factory(db):
    """
    Factory fixture to create Service model instances for tests.
    """

    def _factory(**kwargs):
        defaults = {
            "name": "test-service",
            "bootstrap_secret_ref": "test-secret-ref",
        }
        defaults.update(kwargs)
        return Service.objects.create(**defaults)

    return _factory
