from ninja import Router
from app.common.default.utils import append_data_to_req
from app.endpoints.v1.custom_user import login_ep, profile_ep, profile_from_id_ep
from app.middlewares.default.middleware import logger
from app.middlewares.default.pipeline import pipeline
from django.http import HttpRequest
from app.common.default.standard_response import StandardResponse
from app.schemas.req.custom_user import LoginRequest
from app.schemas.res.custom_user import LoginResponse, ProfileResponse
from app.common.default.responses import responses
from app.common.default.security import JWTAuth
from app.common.default.standard_response import standard_error

v1 = Router(tags=["User"])


@v1.post("/login", response=responses({200: StandardResponse[LoginResponse]}))
def login(request: HttpRequest, credentials: LoginRequest):
    try:
        request = append_data_to_req(request, credentials)
        return pipeline(request, logger, endpoint=login_ep, data=credentials)
    except Exception as e:
        return standard_error(
            status_code=500,
            code=500,
            message=str(e),
            dev=str(e),
        )


@v1.get(
    "/profile",
    response=responses({200: StandardResponse[ProfileResponse]}),
    auth=JWTAuth(),
)
def profile(request: HttpRequest):
    try:
        return pipeline(request, logger, endpoint=profile_ep)
    except Exception as e:
        return standard_error(
            status_code=500,
            code=500,
            message=str(e),
            dev=str(e),
        )


@v1.get("/profile/{id}", response=responses({200: StandardResponse[ProfileResponse]}))
def profile_from_id(request: HttpRequest, id: int):
    try:
        return pipeline(request, logger, endpoint=profile_from_id_ep, data=id)
    except Exception as e:
        return standard_error(
            status_code=500,
            code=500,
            message=str(e),
            dev=str(e),
        )
