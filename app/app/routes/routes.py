from ninja.errors import ValidationError, HttpError, AuthenticationError
from django.http import Http404
from ninja import NinjaAPI
from app.common.default.parser import ORJSONParser
from app.routes.exception_handlers import exception_handler
from app.routes.v1.services import v1 as services_router
from django.conf import settings
from app.routes.openapi import build_openapi_router

v1 = NinjaAPI(
    version="1.0.0",
    title="Template API",
    docs_url="/docs/v1" if settings.DEBUG else None,
    parser=ORJSONParser(),
)


v1.add_router("v1/flume", services_router)

if settings.ENVIRONMENT == "development":
    v1.add_router("v1/openapi", build_openapi_router(v1, protected=False))
elif settings.ENVIRONMENT == "production":
    v1.add_router("v1/openapi", build_openapi_router(v1, protected=True))
else:
    raise ValueError(f"Invalid environment: {settings.ENVIRONMENT}")


@v1.exception_handler(ValidationError)
def validation_errors(request, exc):
    return exception_handler(request, exc, 422)


@v1.exception_handler(HttpError)
def http_errors(request, exc):
    return exception_handler(request, exc, exc.status_code)


@v1.exception_handler(AuthenticationError)
def authentication_errors(request, exc):
    return exception_handler(request, exc, 401)


@v1.exception_handler(Exception)
def general_errors(request, exc):
    return exception_handler(request, exc)


@v1.exception_handler(AttributeError)
def attribute_error(request, exc):
    return exception_handler(request, exc)


@v1.exception_handler(Http404)
def http_404(request, exc):
    return exception_handler(request, exc, 404)
