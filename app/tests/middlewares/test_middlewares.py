import json
import time
import hmac
import hashlib
import pytest
from json import loads
from django.http import JsonResponse
from app.middlewares.bootstrap_verification import bootstrap_verification_mw
from app.schemas.req.services import RegisterRequest
from app.models.services import InboundNonceBootstrap
from app.common.default.globals import (
    MICROSERVICE_INVALID_AUTH,
    MICROSERVICE_INVALID_SIGNATURE,
)


def sign_bootstrap(token: str, ts: int, nonce: str, body: bytes) -> str:
    msg = f"{ts}.{nonce}".encode() + (body or b"")
    sig = hmac.new(token.encode(), msg, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _next_ok() -> JsonResponse:
    return JsonResponse({"ok": True}, status=200)


@pytest.mark.django_db
def test_bootstrap_middleware_happy_path(rf, monkeypatch):
    """
    Tests the successful verification of a bootstrap request.
    It simulates a valid request with correct signature and headers,
    and asserts that the middleware passes the request to the next handler.
    """
    # body e headers
    body_dict = {
        "service_name": "user-svc",
        "base_url": "http://10.0.0.1:8080",
        "bootstrap_secret_ref": "ignored-here",
        "boot_id": "b1",
        "node_id": "n1",
        "task_slot": 1,
        "ttl_s": 300,
        "region": "eu-central-1",
    }
    body = json.dumps(body_dict).encode()
    ts = int(time.time())
    nonce = "abcd" * 8
    token = "s3cr3t"
    sig = sign_bootstrap(token, ts, nonce, body)

    req = rf.post("/flume/register", data=body, content_type="application/json")
    req.headers = {
        "Authorization": f"Bearer {token}",
        "X-Timestamp": str(ts),
        "X-Nonce": nonce,
        "X-Signature": sig,
    }

    data = RegisterRequest(**body_dict)

    # execute
    resp = bootstrap_verification_mw(req, data, _next_ok)
    assert resp.status_code == 200
    # nonce registrato anti-replay
    assert InboundNonceBootstrap.objects.filter(
        service_name="user-svc", nonce=nonce
    ).exists()

    # no auth

    req.headers = {
        "X-Timestamp": str(ts),
        "X-Nonce": nonce,
        "X-Signature": sig,
    }
    resp_no_auth = bootstrap_verification_mw(req, data, _next_ok)
    json_data = loads(resp_no_auth.content)
    assert resp_no_auth.status_code == 400
    assert json_data["code"] == MICROSERVICE_INVALID_AUTH
    assert json_data["message"] == "Invalid auth header"
    assert json_data["dev"] == ""

    req.headers = {
        "Authorization": f"Bearer {token}",
        "X-Timestamp": str(ts),
        "X-Nonce": nonce,
    }
    resp_no_auth = bootstrap_verification_mw(req, data, _next_ok)
    json_data = loads(resp_no_auth.content)
    assert resp_no_auth.status_code == 400
    assert json_data["code"] == MICROSERVICE_INVALID_SIGNATURE
    assert json_data["message"] == "Invalid signature"
    assert json_data["dev"] == ""


@pytest.mark.django_db
def test_bootstrap_middleware_bad_timestamp(rf):
    """
    Tests that the middleware rejects a request with an invalid timestamp.
    """
    body = b"{}"
    req = rf.post("/flume/register", data=body, content_type="application/json")
    req.headers = {
        "Authorization": "Bearer s3cr3t",
        "X-Timestamp": "not-an-int",
        "X-Nonce": "abcd" * 8,
        "X-Signature": "sha256=deadbeef",
    }
    data = RegisterRequest(
        service_name="x",
        base_url="http://10.0.0.1",
        bootstrap_secret_ref="r",
        boot_id="b",
        node_id="n",
        task_slot=1,
        ttl_s=300,
        region="eu",
    )
    resp = bootstrap_verification_mw(req, data, lambda: None)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_bootstrap_middleware_missing_nonce(rf):
    """
    Tests that the middleware rejects a request with a missing nonce.
    """
    req = rf.post("/flume/register", data=b"{}", content_type="application/json")
    req.headers = {
        "Authorization": "Bearer s3cr3t",
        "X-Timestamp": str(int(time.time())),
        "X-Signature": "sha256=deadbeef",
    }
    data = RegisterRequest(
        service_name="x",
        base_url="http://10.0.0.1",
        bootstrap_secret_ref="r",
        boot_id="b",
        node_id="n",
        task_slot=1,
        ttl_s=300,
        region="eu",
    )
    resp = bootstrap_verification_mw(req, data, lambda: None)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_bootstrap_middleware_bad_signature(rf):
    """
    Tests that the middleware rejects a request with an invalid signature.
    """
    body = b'{"service_name":"user-svc","base_url":"http://10.0.0.1"}'
    ts = int(time.time())
    req = rf.post("/flume/register", data=body, content_type="application/json")
    req.headers = {
        "Authorization": "Bearer s3cr3t",
        "X-Timestamp": str(ts),
        "X-Nonce": "abcd" * 8,
        "X-Signature": "sha256=WRONG",
    }
    data = RegisterRequest(
        service_name="user-svc",
        base_url="http://10.0.0.1",
        bootstrap_secret_ref="r",
        boot_id="b",
        node_id="n",
        task_slot=1,
        ttl_s=300,
        region="eu",
    )
    resp = bootstrap_verification_mw(req, data, lambda: None)
    assert resp.status_code == 401
    assert json.loads(resp.content)["code"] == MICROSERVICE_INVALID_SIGNATURE


@pytest.mark.django_db
def test_bootstrap_middleware_replay_nonce(rf):
    """
    Tests that the middleware rejects a request with a replayed nonce.
    It first sends a valid request, and then sends the same request again
    to simulate a replay attack.
    """
    # prima call ok
    body = b'{"service_name":"user-svc","base_url":"http://10.0.0.1"}'
    ts = int(time.time())
    nonce = "abcd" * 8
    token = "s3cr3t"
    sig = sign_bootstrap(token, ts, nonce, body)

    req = rf.post("/flume/register", data=body, content_type="application/json")
    req.headers = {
        "Authorization": f"Bearer {token}",
        "X-Timestamp": str(ts),
        "X-Nonce": nonce,
        "X-Signature": sig,
    }
    data = RegisterRequest(
        service_name="user-svc",
        base_url="http://10.0.0.1",
        bootstrap_secret_ref="r",
        boot_id="b",
        node_id="n",
        task_slot=1,
        ttl_s=300,
        region="eu",
    )
    resp1 = bootstrap_verification_mw(req, data, lambda: JsonResponse({}, status=200))
    assert resp1.status_code == 200

    # seconda call (replay) KO
    req2 = rf.post("/flume/register", data=body, content_type="application/json")
    req2.headers = req.headers
    resp2 = bootstrap_verification_mw(req2, data, lambda: JsonResponse({}, status=200))
    assert resp2.status_code == 401
    assert json.loads(resp2.content)["code"] == MICROSERVICE_INVALID_SIGNATURE
