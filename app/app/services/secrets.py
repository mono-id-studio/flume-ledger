from typing import Dict
from app.models.services import Service
from django.conf import settings
from time import time
from boto3 import client
from json import loads
from typing import Protocol


class SecretsServiceProtocol(Protocol):
    def get(self, service: Service) -> dict | None: ...


class SecretsService:
    CACHES: Dict[str, "SecretsService"] = {}

    _val: Dict | None = None
    _exp = 0.0

    name: str
    ttl_s: int
    region: str

    def __init__(self, name: str, ttl_s: int = 300, region: str | None = None):
        self.name, self.ttl_s, self.region = (
            name,
            ttl_s,
            region or settings.MS_REGION,
        )
        self._val: Dict | None = None
        self._exp = 0.0

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

    def get(self, service: Service) -> dict | None:
        """
        Returns the secrets for the given service.
        """
        now = time()
        if self._val is None or now >= self._exp:
            sm = client("secretsmanager", region_name=self.region)
            resp = sm.get_secret_value(SecretId=self.name)
            raw = resp.get("SecretString") or resp["SecretBinary"].decode()
            self._val = loads(raw)  # es. {"kid":"v1","token":"base64..."}
            self._exp = now + self.ttl_s
        return self._val
