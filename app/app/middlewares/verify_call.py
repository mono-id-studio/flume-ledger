from typing import Any
from app.common.default.globals import (
    MICROSERVICE_INSTANCE_NOT_FOUND,
    MICROSERVICE_INVALID_SIGNATURE,
)
from app.services.services import ServicesService
from django.http import HttpRequest
from app.common.default.standard_response import standard_error
from app.common.default.types import EndPointResponse
from app.middlewares.default.pipeline import NextPipe
from app.services.secrets import SecretsService
from app.services.signer import SignerService


def verify_call(request: HttpRequest, data: Any, next: NextPipe) -> EndPointResponse:
    """
    Resolve a sequence of route handlers.
    """
    ts = int(request.headers["X-Timestamp"])
    nonce = request.headers["X-Nonce"]
    kid = request.headers.get("X-Key-Id", "")
    sig = request.headers["X-Signature"]
    instance_id = request.headers["X-Instance-Id"]
    secrets_svc = SecretsService(
        name=data.service_name,
        ttl_s=data.ttl_s,
        region=data.region,
    )
    signer_svc = SignerService(
        secrets=secrets_svc,
    )
    service_svc = ServicesService(
        secrets=secrets_svc,
        signer=signer_svc,
    )
    instance = service_svc.get_service_instance_by_id(instance_id)
    if instance is None:
        return standard_error(
            status_code=404,
            code=MICROSERVICE_INSTANCE_NOT_FOUND,
            message="Service instance not found",
            dev="Service instance not found",
        )
    service = instance.service
    ok, msg = signer_svc.instance_verification(
        service=service,
        ts=ts,
        nonce=nonce,
        sig=sig,
        kid=kid,
        service_instance=instance,
        body=request.body or b"",
        method=(request.method or "").upper(),
        path_q=request.get_full_path(),
        ts_window=300,
    )
    if not ok:
        return standard_error(
            status_code=401,
            code=MICROSERVICE_INVALID_SIGNATURE,
            message="Invalid signature",
            dev=msg,
        )

    response = next()
    print("Verify call done")
    return response
