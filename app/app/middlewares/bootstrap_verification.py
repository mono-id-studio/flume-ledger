from app.common.default.globals import (
    MICROSERVICE_INVALID_AUTH,
    MICROSERVICE_INVALID_NONCE,
    MICROSERVICE_INVALID_SIGNATURE,
    MICROSERVICE_INVALID_TIMESTAMP,
)
from app.schemas.req.services import RegisterRequest
from django.http import HttpRequest
from app.common.default.standard_response import standard_error
from app.common.default.types import EndPointResponse
from app.middlewares.default.pipeline import NextPipe
from app.services.secrets import SecretsService
from app.services.signer import SignerService


def bootstrap_verification_mw(
    request: HttpRequest, data: RegisterRequest, next: NextPipe
) -> EndPointResponse:
    """
    Resolve a sequence of route handlers.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_AUTH,
            message="Invalid auth header",
            dev="Authorization must be 'Bearer <token>'",
        )
    token = auth.split(" ")[1]
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

    # Signature
    sig = request.headers.get("X-Signature")
    if not sig:
        return standard_error(
            status_code=400,
            code=MICROSERVICE_INVALID_SIGNATURE,
            message="Invalid signature",
            dev="Missing X-Signature",
        )
    signer_svc = SignerService(
        secrets=SecretsService,
    )

    ok, msg = signer_svc.bootstrap_verification(
        service_name=data.service_name,
        token=token,
        ts=ts,
        nonce=nonce,
        signature=sig,
        body=request.body or b"",
    )
    if not ok:
        return standard_error(
            status_code=401,
            code=MICROSERVICE_INVALID_SIGNATURE,
            message="Invalid signature",
            dev=msg,
        )

    return next()
