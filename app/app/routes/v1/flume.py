from ninja import Router
from app.endpoints.v1.flume import deregister_ep, register_ep
from django.http import HttpRequest
from app.schemas.req.flume import RegisterRequest
from app.middlewares.default.pipeline import pipeline

v1 = Router(tags=["Flume"])


@v1.post("/services/register")
def register(request: HttpRequest, data: RegisterRequest):
    return pipeline(request, endpoint=register_ep, data=data)


@v1.delete("/services/{service_id}/instances/{instance_id}")
def deregister(request: HttpRequest, service_id: str, instance_id: str):
    return pipeline(request, endpoint=deregister_ep, data={service_id, instance_id})
