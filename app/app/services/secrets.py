from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Protocol, runtime_checkable
from datetime import datetime, timedelta
from time import time
from json import loads
from base64 import b64decode
from boto3 import client
from django.conf import settings
from app.models.services import Service


@dataclass
class SecretObject:
    token: str
    kid: str
    prev_token: str | None
    prev_kid: str | None
    rotated_at: datetime
    accept_prev_until: datetime


@runtime_checkable
class SecretsServiceProtocol(Protocol):
    @staticmethod
    def token_to_bytes(token: str) -> bytes: ...
    @staticmethod
    def get(
        service: Service, ttl_s: int = 300, region: str | None = None
    ) -> SecretObject | None: ...
    @staticmethod
    def get_current(service: Service) -> Tuple[str, bytes] | None: ...
    @staticmethod
    def get_previous(service: Service) -> Tuple[str, bytes] | None: ...


class SecretsService:
    cache: Dict[str, SecretObject] = {}

    @staticmethod
    def token_to_bytes(token: str) -> bytes:
        if token.startswith("base64:"):
            return b64decode(token.split(":", 1)[1])
        return token.encode("utf-8")

    @staticmethod
    def get(
        service: Service, ttl_s: int = 300, region: str | None = None
    ) -> SecretObject | None:
        ref = service.bootstrap_secret_ref
        if not ref:
            return None

        if ref in SecretsService.cache:
            return SecretsService.cache[ref]

        sm = client("secretsmanager", region_name=region or settings.MS_REGION)
        resp = sm.get_secret_value(SecretId=ref)
        raw = resp.get("SecretString") or resp["SecretBinary"].decode()
        data = loads(
            raw
        )  # es: {"kid":"v1","token":"base64:...", "prev_token": "...", "prev_kid": "..."}

        now = datetime.now()
        obj = SecretObject(
            token=data["token"],
            kid=data["kid"],
            prev_token=data.get("prev_token"),
            prev_kid=data.get("prev_kid"),
            rotated_at=now,
            accept_prev_until=now + timedelta(seconds=ttl_s),
        )
        SecretsService.cache[ref] = obj
        return obj

    @staticmethod
    def get_current(service: Service) -> Tuple[str, bytes] | None:
        val = SecretsService.get(service)
        if not val:
            return None
        return val.kid, SecretsService.token_to_bytes(val.token)

    @staticmethod
    def get_previous(service: Service) -> Tuple[str, bytes] | None:
        val = SecretsService.get(service)
        if not val or not (val.prev_kid and val.prev_token):
            return None
        return val.prev_kid, SecretsService.token_to_bytes(val.prev_token)
