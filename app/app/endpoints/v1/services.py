from app.common.default.utils import set_if_diff
from app.models.services import ServiceInstance
from app.services.services import ServicesService
from app.services.register_state import RegistryStateService
from app.services.secrets import SecretsService
from app.services.signer import SignerService
from django.http import HttpRequest
from app.common.default.standard_response import standard_error, standard_response
from app.common.default.types import EndPointResponse
from app.schemas.req.services import RegisterRequest
from app.schemas.res.services import RegisterResponse
from django.db.transaction import atomic
from django.conf import settings


def register_ep(request: HttpRequest, data: RegisterRequest) -> EndPointResponse:
    try:
        with atomic():
            secrets_svc = SecretsService(
                name=data.service_name,
                ttl_s=data.ttl_s,
                region=data.region,
            )
            signer_svc = SignerService(
                secrets=secrets_svc,
            )
            service_svc = ServicesService(secrets=secrets_svc, signer=signer_svc)
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

            # bump version only if something changed (creation or update)
            changed = created  # + eventuali changed sopra
            version = RegistryStateService().maybe_bump(changed)

        # (outside transaction) fanout of the registry, if you want
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
    except Exception as e:
        return standard_error(
            status_code=500,
            message="Internal server error",
            code=500,
            dev=str(e) if settings.DEBUG else "",
        )
