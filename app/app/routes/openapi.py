# urls.py
from django.http import JsonResponse
from ninja import Router, NinjaAPI
from ninja.errors import AuthenticationError


def build_openapi_router(api: NinjaAPI, protected: bool = False):
    v1 = Router(tags=["Services API"])

    @v1.get("/openapi.json")
    def openapi_for_apidog(request):
        if protected:
            raise AuthenticationError("Unauthorized")
        schema = api.get_openapi_schema()
        return JsonResponse(schema)

    return v1
