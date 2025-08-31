# tests/common/test_base_model.py
import time
from app.models.register import RegistryState
import pytest
from django.forms import model_to_dict

from app.models.services import Service, ServiceInstance


@pytest.mark.django_db
def test_basemodel_dict_matches_model_to_dict():
    svc = Service.objects.create(
        name="user-svc",
        bootstrap_secret_ref="secret/ref",
    )
    # BaseModel.dict deve equivalere a model_to_dict
    assert svc.dict() == model_to_dict(svc)


@pytest.mark.django_db
def test_basemodel_relation_returns_fk_object():
    svc = Service.objects.create(
        name="order-svc",
        bootstrap_secret_ref="secret/ref",
    )
    inst = ServiceInstance.objects.create(
        service=svc,
        node_id="n1",
        task_slot=1,
        boot_id="b1",
        base_url="http://10.0.0.1:8080/",
        health_url="http://10.0.0.1:8080/health",
        heartbeat_interval_sec=10,
    )

    assert inst.relation("service") is svc
    assert inst.relation("base_url") == "http://10.0.0.1:8080/"


@pytest.mark.django_db
def test_basemodel_timestamps_autoset_and_updated():
    svc = Service.objects.create(
        name="billing-svc",
        bootstrap_secret_ref="secret/ref",
    )

    assert svc.created_at is not None
    assert svc.updated_at is not None
    assert svc.updated_at >= svc.created_at

    time.sleep(1)
    svc.meta = {"owner": "team-x"}
    svc.save(update_fields=["meta", "updated_at"])

    svc.refresh_from_db()
    assert svc.updated_at > svc.created_at


@pytest.mark.django_db
def test_service_str():
    svc = Service.objects.create(
        name="billing-svc",
        bootstrap_secret_ref="secret/ref",
    )
    assert str(svc) == "billing-svc"


@pytest.mark.django_db
def test_service_instance_str():
    svc = Service.objects.create(
        name="billing-svc",
        bootstrap_secret_ref="secret/ref",
    )
    inst = ServiceInstance.objects.create(
        service=svc,
        node_id="n1",
        task_slot=1,
        boot_id="b1",
        base_url="http://10.0.0.1:8080/",
        health_url="http://10.0.0.1:8080/health",
        heartbeat_interval_sec=10,
    )
    assert str(inst) == "billing-svc@http://10.0.0.1:8080/"


@pytest.mark.django_db
def test_registry_state_str():
    reg = RegistryState.objects.create(
        registry_version=1,
    )
    assert reg.registry_version == 1
    assert reg.pk == 1
    assert reg.pkid == 1

    assert reg.maybe_bump(False) == 1
    reg.refresh_from_db()
    assert reg.registry_version == 1

    assert reg.maybe_bump(True) == 2
    reg.refresh_from_db()
    assert reg.registry_version == 2


@pytest.mark.django_db
def test_registry_state_not_found():
    reg = RegistryState.objects.create(
        registry_version=1,
        pkid=2,
    )
    assert reg.current() == 0
