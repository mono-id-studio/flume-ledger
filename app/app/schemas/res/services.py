from typing import List
from ninja import Schema


class RegisterResponse(Schema):
    service_id: str
    instance_id: str
    push_kid: str
    lease_ttl_sec: int
    registry_version: int


class ServiceInstanceSnapshot(Schema):
    instance_id: str
    base_url: str
    status: str
    meta: dict


class Capabilities(Schema):
    publishes: List[str]
    consumes: List[str]


class ServiceSnapshot(Schema):
    service_id: str
    name: str
    capabilities: Capabilities
    meta: dict
    instances: list[ServiceInstanceSnapshot]


class ServiceSnapshotResponse(Schema):
    version: int
    services: list[ServiceSnapshot]
