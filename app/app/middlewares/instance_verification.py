from app.common.default.globals import (
    MICROSERVICE_INVALID_NONCE,
    MICROSERVICE_INVALID_SIGNATURE,
    MICROSERVICE_INVALID_TIMESTAMP,
    MICROSERVICE_INVALID_KID,
    MICROSERVICE_INVALID_INSTANCE,
)
from django.http import HttpRequest
from app.common.default.standard_response import standard_error
from app.common.default.types import EndPointResponse
from app.middlewares.default.pipeline import NextPipe
from app.services.secrets import SecretsService
from app.services.signer import SignerService
from app.services.services import ServicesService


def instance_verification_mw(
    request: HttpRequest, data, next: NextPipe
) -> EndPointResponse:
    """
    HMAC verification for calls from a registered instance (client -> ledger).
    Requires headers:
      - X-Timestamp: <epoch int>
      - X-Nonce: <hex>
      - X-Key-Id: <kid>
      - X-Signature: sha256=<hex>
      - (optional but useful) X-Instance-Id: <uuid> if the endpoint does not have it in the body/path
    """
    # Timestamp
    ts_raw = request.headers.get("X-Timestamp")
    try:
        ts = int(ts_raw or "")
    except (TypeError, ValueError):
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_TIMESTAMP,
            message="Invalid timestamp",
            dev=f"Invalid X-Timestamp: {ts_raw!r}",
        )

    # Nonce
    nonce = request.headers.get("X-Nonce")
    if not nonce:
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_NONCE,
            message="Invalid nonce",
            dev="Missing X-Nonce",
        )

    # Key ID (mandatory in strict mode)
    kid = request.headers.get("X-Key-Id")
    if not kid:
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_KID,
            message="Invalid kid",
            dev="Missing X-Key-Id",
        )

    # Signature
    sig = request.headers.get("X-Signature")
    if not sig:
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_SIGNATURE,
            message="Invalid signature",
            dev="Missing X-Signature",
        )

    # Find the instance: header > body (schema) > (optional) query
    instance_id = (
        request.headers.get("X-Instance-Id")
        or getattr(data, "instance_id", None)
        or request.GET.get("instance_id")
    )
    if not instance_id:
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_INSTANCE,
            message="Missing instance id",
            dev="Provide X-Instance-Id header or body/query 'instance_id'",
        )

    signer = SignerService(secrets=SecretsService)
    svc = ServicesService(secrets=SecretsService, signer=signer)

    inst = svc.get_service_instance_by_id(instance_id)
    if inst is None:
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_INSTANCE,
            message="Unknown instance",
            dev=f"ServiceInstance {instance_id} not found",
        )

    ok, msg = signer.instance_verification(
        service=inst.service,
        ts=ts,
        nonce=nonce,
        signature=sig,
        kid=kid,
        service_instance=inst,
        body=(request.body or b""),
        method=request.method or "GET",
        path_q=request.get_full_path(),  # includes the query string
        ts_window=300,
    )
    if not ok:
        return standard_error(
            status_code=401,
            code=MICROSERVICE_INVALID_SIGNATURE,
            message="Invalid signature",
            dev=msg,
        )

    return next()
