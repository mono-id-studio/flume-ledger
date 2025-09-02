from app.models.events import EventDefinition
import pytest
from django.test import RequestFactory
from app.models.services import Service, ServiceInstance


@pytest.fixture
def rf() -> RequestFactory:
    """
    Fixture for Django's RequestFactory.
    """
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
            "active_kid": "v1",
        }
        defaults.update(kwargs)
        return Service.objects.create(**defaults)

    return _factory


@pytest.fixture
def service_instance_factory(db, service_factory):
    """
    Factory fixture to create ServiceInstance model instances for tests.
    """

    def _factory(**kwargs):
        if "service" not in kwargs:
            kwargs["service"] = service_factory()

        defaults = {
            "base_url": "http://test-service.local",
            "health_url": "http://test-service.local/health",
        }
        defaults.update(kwargs)
        return ServiceInstance.objects.create(**defaults)

    return _factory
