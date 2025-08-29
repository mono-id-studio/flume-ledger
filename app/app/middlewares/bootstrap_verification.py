from app.common.default.globals import (
    MICROSERVICE_INVALID_SIGNATURE,
)
from app.schemas.req.services import RegisterRequest
from django.http import HttpRequest
from app.common.default.standard_response import standard_error
from app.common.default.types import EndPointResponse
from app.middlewares.default.pipeline import NextPipe
from app.services.secrets import SecretsService
from app.services.signer import SignerService


def bootstrap_verification(
    request: HttpRequest, data: RegisterRequest, next: NextPipe
) -> EndPointResponse:
    """
    Resolve a sequence of route handlers.
    """
    token = request.headers["Authorization"]
    token = token.split(" ")[1]
    ts = int(request.headers["X-Timestamp"])
    nonce = request.headers["X-Nonce"]
    kid = request.headers.get("X-Key-Id", "")
    sig = request.headers["X-Signature"]
    secrets_svc = SecretsService(
        name=data.service_name,
        ttl_s=data.ttl_s,
        region=data.region,
    )
    signer_svc = SignerService(
        secrets=secrets_svc,
    )

    ok, msg = signer_svc.bootstrap_verification(
        token=token,
        ts=ts,
        nonce=nonce,
        kid=kid,
        signature=sig,
    )
    if not ok:
        return standard_error(
            status_code=401,
            code=MICROSERVICE_INVALID_SIGNATURE,
            message="Invalid signature",
            dev=msg,
        )

    response = next()
    return response
