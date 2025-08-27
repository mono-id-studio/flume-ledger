from app.common.default.utils import set_if_diff
from app.models.services import ServiceInstance
from app.services.services import ServicesService
from app.services.register_state import RegistryStateService
from django.http import HttpRequest
from app.common.default.standard_response import standard_response
from app.common.default.types import EndPointResponse
from app.schemas.req.services import RegisterRequest
from app.schemas.res.services import RegisterResponse
from django.db.transaction import atomic


def register_ep(request: HttpRequest, data: RegisterRequest) -> EndPointResponse:
    with atomic():
        service_svc = ServicesService()
        svc = service_svc.get_or_create_service(
            data.service_name, data.bootstrap_secret_ref
        )

        # dedup per (service, node_id, task_slot)
        inst = None
        if data.node_id and data.task_slot is not None:
            inst = service_svc.get_same_instance_after_reboot(
                svc, data.node_id, data.task_slot
            )

        created = False
        if inst is None:
            inst = service_svc.create_service_instance(svc, data)
            created = True
        else:
            changed = False
            changed |= set_if_diff(inst, "base_url", data.base_url)
            changed |= set_if_diff(
                inst,
                "health_url",
                data.health_url or (str(data.base_url).rstrip("/") + "/health"),
            )
            changed |= set_if_diff(
                inst, "heartbeat_interval_sec", data.heartbeat_interval_sec
            )
            incoming_boot = getattr(data.meta, "boot_id", None)
            if incoming_boot and incoming_boot != inst.boot_id:
                inst.boot_id = incoming_boot
                inst.status = ServiceInstance.Status.UP
                inst.consecutive_miss = 0
                changed = True
            if changed:
                inst.push_kid = svc.active_kid
                inst.save()

        # bump versione solo se è cambiato qualcosa (creazione o update)
        changed = created  # + eventuali changed sopra
        version = RegistryStateService().maybe_bump(changed)

    # (fuori transazione) fanout del registro, se vuoi
    # if changed: enqueue_push_registry(version, scope="all")

    return standard_response(
        status_code=200,
        message="Flume endpoint",
        data=RegisterResponse(
            service_id=str(svc.service_id),
            instance_id=str(inst.instance_id),  # ← importante
            push_kid=inst.push_kid,  # ← per coerenza firme
            lease_ttl_sec=data.heartbeat_interval_sec * 3,  # esempio
            registry_version=version,
        ),
    )


def deregister_ep(request: HttpRequest, data: dict) -> EndPointResponse:
    service_id = data["service_id"]
    instance_id = data["instance_id"]
    return standard_response(
        status_code=200,
        message="Flume endpoint",
        data={
            "service_id": service_id,
            "instance_id": instance_id,
        },
    )
