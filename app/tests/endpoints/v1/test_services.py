import json
import pytest
from app.endpoints.v1.services import register_ep
from app.models.services import Service, ServiceInstance
from app.schemas.req.services import RegisterRequest


@pytest.fixture
def register_request_data() -> dict:
    """
    Provides a dictionary of valid data for a RegisterRequest.
    """
    return {
        "service_name": "test-service",
        "base_url": "http://10.0.1.11:8080/",  # must end with a slash because the schema use AnyHttpUrl
        "health_url": "http://10.0.1.11:8080/health",
        "heartbeat_interval_sec": 10,
        "bootstrap_secret_ref": "some-secret-ref",
        "boot_id": "boot-123",
        "node_id": "node-abc",
        "task_slot": 1,
        "ttl_s": 300,
        "region": "eu-central-1",
    }


@pytest.mark.django_db(transaction=True)
def test_register_ep_new_service_and_instance(rf, monkeypatch, register_request_data):
    """
    Tests the happy path for registering a completely new service and instance.
    """
    # Mock the RegistryStateService to avoid external dependencies
    monkeypatch.setattr(
        "app.endpoints.v1.services.RegistryStateService.maybe_bump",
        lambda self, changed: 1,
    )

    request = rf.post(
        "/register", data=register_request_data, content_type="application/json"
    )
    data_obj = RegisterRequest(**register_request_data)

    # Execute the endpoint
    response = register_ep(request, data_obj)

    # Assertions for database state
    assert Service.objects.count() == 1
    assert ServiceInstance.objects.count() == 1
    service = Service.objects.first()
    instance = ServiceInstance.objects.first()
    assert service.name == register_request_data["service_name"]
    assert instance.service == service

    # Assertions for the HTTP response
    assert response.status_code == 200
    response_data = json.loads(response.content)
    assert response_data["data"]["service_id"] == str(service.service_id)
    assert response_data["data"]["instance_id"] == str(instance.instance_id)
    assert response_data["data"]["registry_version"] == 1


@pytest.mark.django_db(transaction=True)
def test_register_ep_existing_instance_update(
    rf, monkeypatch, service_instance_factory, register_request_data
):
    """
    Tests the happy path for re-registering and updating an existing instance.
    """
    # Create an initial instance to be updated
    existing_instance = service_instance_factory(
        node_id=register_request_data["node_id"],
        task_slot=register_request_data["task_slot"],
        base_url="http://old.url/path",
    )
    service = existing_instance.service

    # Mock the RegistryStateService
    monkeypatch.setattr(
        "app.endpoints.v1.services.RegistryStateService.maybe_bump",
        lambda self, changed: 2,  # Assume version bumps to 2
    )

    request = rf.post(
        "/register", data=register_request_data, content_type="application/json"
    )
    data_obj = RegisterRequest(**register_request_data)

    # Execute the endpoint
    response = register_ep(request, data_obj)

    # Assertions for database state (no new objects should be created)
    assert Service.objects.count() == 1
    assert ServiceInstance.objects.count() == 1

    # Assert that the instance was updated
    existing_instance.refresh_from_db()
    assert existing_instance.base_url == register_request_data["base_url"]

    # Assertions for the HTTP response
    assert response.status_code == 200
    response_data = json.loads(response.content)
    assert response_data["data"]["service_id"] == str(service.service_id)
    assert response_data["data"]["instance_id"] == str(existing_instance.instance_id)
    assert response_data["data"]["registry_version"] == 2
