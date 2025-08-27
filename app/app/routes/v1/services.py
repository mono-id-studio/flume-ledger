from app.common.default.responses import (
    responses,
    StandardResponse,
)
from ninja import Router
from app.endpoints.v1.services import register_ep
from django.http import HttpRequest
from app.schemas.req.services import RegisterRequest
from app.middlewares.default.pipeline import pipeline
from app.schemas.res.services import RegisterResponse

v1 = Router(tags=["Services API"])


@v1.post(
    "/services/register",
    response=responses(
        {
            200: StandardResponse[RegisterResponse],
        }
    ),
    description="Register a new service or add a new instance to an existing service",
    summary="Register a new service or add a new instance to an existing service",
)
def register(request: HttpRequest, data: RegisterRequest):
    return pipeline(request, endpoint=register_ep, data=data)
