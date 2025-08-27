from asyncio import gather
from httpx import AsyncClient, put
from json import dumps
from app.models.services import Service, ServiceInstance
from app.schemas.req.services import RegisterRequest
from app.schemas.res.services import (
    ServiceInstanceSnapshot,
    ServiceSnapshot,
    ServiceSnapshotResponse,
)
from app.schemas.res.services import Capabilities
from app.services.signer import SignService
from django.db.models import Q


class ServicesService:
    def get_or_create_service(
        self, service_name: str, bootstrap_secret_ref: str
    ) -> Service:
        return Service.objects.get_or_create(
            name=service_name, defaults={"bootstrap_secret_ref": bootstrap_secret_ref}
        )

    def get_same_instance_after_reboot(
        srv: Service, node_id: str, task_slot: int
    ) -> ServiceInstance:
        return ServiceInstance.objects.filter(
            service=srv,
            node_id=node_id,
            task_slot=task_slot,
        ).first()

    def create_service_instance(srv: Service, data: RegisterRequest) -> ServiceInstance:
        return ServiceInstance.objects.create(
            service=srv,
            name=data.service_name,
            node_id=data.meta.node_id,
            task_slot=data.meta.task_slot,
            boot_id=data.meta.boot_id,
            base_url=data.base_url,
            health_url=data.health_url,
            heartbeat_interval_sec=data.heartbeat_interval_sec,
            status=ServiceInstance.Status.UP,
            push_kid=srv.active_kid,
            meta=(data.meta.dict() if data.meta else {}),
        )

    async def push_new_ledger_to_all_instances(self, version: int):
        # instances UP
        targets = list(
            ServiceInstance.objects.filter(Q(status=ServiceInstance.Status.UP))
        )
        # costruisci body UNA volta
        payload: ServiceSnapshotResponse = self.build_registry_snapshot(version)
        body = dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()

        results = []
        async with AsyncClient(timeout=(2, 10), follow_redirects=False) as client:
            tasks = [
                self.push_new_ledger_to_one_instances(client, inst, body, version)
                for inst in targets
            ]
            results = await gather(*tasks, return_exceptions=False)

        ok = sum(1 for _, code, _ in results if 200 <= code < 300)
        fail = [r for r in results if not (200 <= r[1] < 300)]
        return (len(targets), ok, fail)

    def push_new_ledger_to_one_instances(
        inst: ServiceInstance, body_bytes: bytes, version: int
    ):
        url = inst.base_url.rstrip("/") + "/flume/registry"
        sign_service = SignService()
        headers = sign_service.signed_headers_for(inst, body_bytes)
        headers["X-Registry-Version"] = str(version)
        try:
            r = put(
                url,
                data=body_bytes,
                headers=headers,
                timeout=(2, 10),
                allow_redirects=False,
            )
            return (str(inst.instance_id), r.status_code, "")
        except Exception as e:
            return (str(inst.instance_id), 0, str(e))

    def build_registry_snapshot(version: int) -> ServiceSnapshotResponse:
        services: list[Service] = []
        svc_qs = Service.objects.all().only(
            "service_id", "name", "publishes", "consumes", "meta"
        )
        inst_qs = ServiceInstance.objects.select_related("service").only(
            "instance_id", "service", "base_url", "status", "meta"
        )
        inst_by_service = {}
        for i in inst_qs:
            instance: ServiceInstanceSnapshot = ServiceInstanceSnapshot(
                instance_id=str(i.instance_id),
                base_url=i.base_url,
                status=i.status,
                meta=i.meta or {},
            )
            inst_by_service.setdefault(i.service_id, []).append(instance)
        for s in svc_qs:
            services.append(
                ServiceSnapshot(
                    service_id=str(s.service_id),
                    name=s.name,
                    capabilities=Capabilities(
                        publishes=s.publishes or [],
                        consumes=s.consumes or [],
                    ),
                    meta=s.meta or {},
                    instances=inst_by_service.get(s.service_id, []),
                )
            )

        return ServiceSnapshotResponse(version=version, services=services)
