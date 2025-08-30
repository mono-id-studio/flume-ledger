from datetime import datetime
from typing import Dict, Tuple
from app.models.services import Service
from django.conf import settings
from time import time
from boto3 import client
from json import loads
from typing import Protocol
from base64 import b64decode

class SecretsServiceProtocol(Protocol):
    def get_current(self, service: Service) -> Tuple[str, bytes] | None: ...
    def get_previous(self, service: Service) -> Tuple[str, bytes] | None: ...


class SecretObject:
    token: str,
    kid: str,
    prev_token: str,
    prev_kid: str,
    rotated_at: datetime
    accept_prev_until: datetime

class SecretsService:
    cache: Dict[str, "SecretObject"] = {}

    @staticmethod
    def token_to_bytes(token: str) -> bytes:
        return (
            b64decode(token.split(":", 1)[1])
            if token.startswith("base64:")
            else token.encode("utf-8")
        )

    @staticmethod
    def _get_cache_for_service(service: Service) -> "SecretsService":
        """
        Returns a SecretsService instance for the given service.
        If the service is not in the cache, it creates a new instance and adds it to the cache.
        """
        if service.bootstrap_secret_ref not in SecretsService.CACHES:
            SecretsService.CACHES[service.bootstrap_secret_ref] = SecretsService(
                service.bootstrap_secret_ref,
                ttl_s=service.ttl_s,
                region=service.region,
            )
        return SecretsService.CACHES[service.bootstrap_secret_ref]

    @staticmethod
    def get(service: Service, ttl_s: int = 300, region: str | None = None) -> SecretObject | None:
        """
        Returns the secrets for the given service.
        """
        if service.bootstrap_secret_ref in SecretsService.cache:
            return SecretsService.cache[service.bootstrap_secret_ref]
        else:
            
            sm = client("secretsmanager", region_name=region or settings.MS_REGION)
            resp = sm.get_secret_value(SecretId=service.bootstrap_secret_ref)
            raw = resp.get("SecretString") or resp["SecretBinary"].decode()
            val = loads(raw)  # es. {"kid":"v1","token":"base64..."}
            now = time()
            SecretsService.cache[service.bootstrap_secret_ref] = SecretObject(
                token=val["token"],
                kid=val["kid"],
                prev_token=val["prev_token"],
                prev_kid=val["prev_kid"],
                rotated_at=now,
                accept_prev_until=now + ttl_s,
            )
            return val

    @staticmethod
    def get_current(service: Service) -> Tuple[str, bytes] | None:
        """
        Returns the secrets for the given service.
        """
        val: SecretObject = SecretsService.get(service)
        return val.kid, SecretsService.token_to_bytes(val.token)

    @staticmethod
    def get_previous(service: Service) -> Tuple[str, bytes] | None:
        """
        Returns the previous secrets for the given service.
        """
        val: SecretObject = SecretsService.get(service)
        return val.prev_kid, SecretsService.token_to_bytes(val.prev_token)
