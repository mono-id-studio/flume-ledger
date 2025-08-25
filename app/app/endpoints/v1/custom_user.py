from django.http import HttpRequest
from app.common.default.standard_response import standard_response
from app.common.default.types import EndPointResponse
from app.common.default.utils import get_user_from_request
from app.models.custom_user import CustomUser
from app.schemas.req.custom_user import LoginRequest
from app.schemas.res.custom_user import ProfileResponse


def login_ep(request: HttpRequest, data: LoginRequest) -> EndPointResponse:
    # user = authenticate(
    #     request,
    #     username=data.email,
    #     password=data.password,
    # )
    return standard_response(
        status_code=200,
        message="Login successful",
        data={},
    )
    # if user is None:
    #     return standard_response(
    #         status_code=401,
    #         data=None,
    #         message="Invalid credentials",
    #     )
    # user_service: CustomUserService = CustomUserService(
    #     jwt_secret_key=settings.JWT_SECRET_KEY,
    #     jwt_algorithm=settings.JWT_ALGORITHM,
    #     jwt_expiration_time=settings.JWT_EXPIRATION_TIME,
    #     jwt_refresh_expiration_time=settings.JWT_REFRESH_EXPIRATION_TIME,
    # )
    # token = user_service.generate_jwt_token(getattr(user, "id"))
    # refresh_token = user_service.generate_refresh_jwt_token(getattr(user, "id"))
    # response = LoginResponse(
    #     access_token=token,
    #     refresh_token=refresh_token,
    # )
    # return standard_response(
    #     status_code=200,
    #     message="Login successful",
    #     data=response,
    # )


def profile_ep(request: HttpRequest) -> EndPointResponse:
    user = get_user_from_request(request)
    if user is None:
        return standard_response(
            status_code=401,
            data=None,
            message="Unauthorized",
        )
    response: ProfileResponse = ProfileResponse(
        id=getattr(user, "id"),
        email=getattr(user, "email"),
        first_name=getattr(user, "first_name"),
        last_name=getattr(user, "last_name"),
        groups=[group.name for group in user.groups.all()],
    )
    return standard_response(
        status_code=200,
        message="Profile",
        data=response,
    )


def profile_from_id_ep(request: HttpRequest, data: int) -> EndPointResponse:
    user = CustomUser.objects.get(id=data)
    response: ProfileResponse = ProfileResponse(
        id=user.ID(),
        email=str(user.email),
        first_name=str(user.first_name),
        last_name=str(user.last_name),
        groups=[],
    )
    return standard_response(
        status_code=200,
        message="Profile",
        data=response,
    )
