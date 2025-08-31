from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Protocol, runtime_checkable
from datetime import datetime, timedelta
from json import loads
from boto3 import client
from django.conf import settings
from app.models.services import Service
from app.common.default.security import token_to_bytes


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
    def get(
        service: Service, ttl_s: int = 300, region: str | None = None
    ) -> SecretObject | None:
        ref: str = service.bootstrap_secret_ref

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
        return val.kid, token_to_bytes(val.token)

    @staticmethod
    def get_previous(service: Service) -> Tuple[str, bytes] | None:
        val = SecretsService.get(service)
        if not val or not (val.prev_kid and val.prev_token):
            return None
        return val.prev_kid, token_to_bytes(val.prev_token)
