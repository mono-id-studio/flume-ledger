from typing import Mapping, Tuple
from app.models.services import Service, ServiceInstance
from app.services.secrets import SecretsService
from time import time
from os import urandom
from hmac import new
from hashlib import sha256
from base64 import b64decode


class SignerService:
    def signed_headers_for(
        self,
        instance: ServiceInstance,
        method: str,
        path_with_query: str,
        body: bytes = b"",
    ) -> Mapping[str, str]:
        """
        Returns the signed headers for the given instance and body.
        """
        service = instance.service
        kid, token_bytes = self.get_active_kid_and_token(service)

        ts = int(time())
        nonce = urandom(16).hex()
        key = self.derive_instance_key(token_bytes, str(instance.instance_id))
        msg = (f"{method.upper()}\n{path_with_query}\n{ts}\n{nonce}\n").encode() + (
            body or b""
        )
        sig = new(key, msg, sha256).hexdigest()

        return {
            "X-Timestamp": str(ts),
            "X-Nonce": nonce,
            "X-Signature": f"sha256={sig}",
            "X-Key-Id": kid,  # importante per rotazioni
            "X-Signed-Method": method.upper(),
            "X-Signed-Path-With-Query": path_with_query,
            "Content-Type": "application/json",
        }

    def get_active_kid_and_token(self, service: Service) -> Tuple[str, bytes]:
        """
        Returns the active kid and token for the given service.
        """
        data = SecretsService._get_cache_for_service(service).get()
        if data is None:
            raise ValueError("No secrets found for service")
        kid = data["kid"]
        token = data["token"]
        token_bytes: bytes = b""
        if token.startswith("base64:"):
            token_bytes = b64decode(token.split(":", 1)[1])
        else:
            token_bytes = token.encode()
        return kid, token_bytes

    def derive_instance_key(self, token_bytes: bytes, instance_id: str) -> bytes:
        """
        Returns the instance key for the given token and instance id.
        """
        # chiave per-istanza: HMAC(token, "push:"+instance_id)
        return new(token_bytes, ("push:" + instance_id).encode(), sha256).digest()
