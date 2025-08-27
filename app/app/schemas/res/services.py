from ninja import Schema


class RegisterResponse(Schema):
    service_id: str
    instance_id: str
    push_kid: str
    lease_ttl_sec: int
    registry_version: int
