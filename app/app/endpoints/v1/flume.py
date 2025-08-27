from django.http import HttpRequest
from app.common.default.standard_response import standard_response
from app.common.default.types import EndPointResponse
from app.schemas.req.flume import RegisterRequest
from app.schemas.res.flume import RegisterResponse


def register_ep(request: HttpRequest, data: RegisterRequest) -> EndPointResponse:
    return standard_response(
        status_code=200,
        message="Flume endpoint",
        data=RegisterResponse(
            service_id=data,
            lease_ttl_sec=data.heartbeat_interval_sec,
            registry_version=1,
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
