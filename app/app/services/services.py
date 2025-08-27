from os import name
from app.models.services import Service, ServiceInstance
from app.schemas.req.services import RegisterRequest


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

    def push_new_ledger_to_all_instances():
        pass

    def push_new_ledger_to_one_instances(srv: Service):
        pass
