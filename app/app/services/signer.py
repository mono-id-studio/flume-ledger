from typing import Mapping, Tuple
from app.models.services import InboundNounce, Service, ServiceInstance
from app.services.services import ServicesProtocol
from app.services.secrets import SecretsProtocol
from time import time
from os import urandom
from hmac import new, compare_digest
from hashlib import sha256
from base64 import b64decode
from typing import Protocol


class SignerProtocol(Protocol):
    def signed_headers_for(
        self,
        instance: ServiceInstance,
        method: str,
        path_with_query: str,
        body: bytes = b"",
    ) -> Mapping[str, str]: ...

    def get_active_kid_and_token(self, service: Service) -> Tuple[str, bytes]: ...

    def derive_instance_key(self, token_bytes: bytes, instance_id: str) -> bytes: ...

    def verify_ts_window(self, ts: int, ts_window: int = 300) -> bool: ...

    def verify_client_call(
        self,
        service: Service,
        ts: int,
        nonce: str,
        sig: str,
        kid: str,
        service_instance: ServiceInstance,
        body: bytes = b"",
        method: str = "GET",
        path_q: str = "",
        ts_window: int = 300,
    ) -> tuple[bool, str]: ...


class SignerService:
    def __init__(self, secrets: SecretsProtocol):
        self.secrets = secrets

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
        data = self.secrets.get(service)
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

    def verify_ts_window(self, ts: int, ts_window: int = 300) -> bool:
        """
        Returns True if the timestamp is within the window.
        """
        return abs(time() - ts) <= ts_window

    def verify_client_call(
        self,
        service: Service,
        ts: int,
        nonce: str,
        sig: str,
        kid: str,
        service_instance: ServiceInstance,
        body: bytes = b"",
        method: str = "GET",
        path_q: str = "",
        ts_window: int = 300,
    ) -> tuple[bool, str]:
        is_valid = self.verify_ts_window(ts, ts_window)
        if not is_valid:
            return False, "timestamp window"

        # anti-replay: save nonce for 5 min (cache/DB); example DB:
        try:
            InboundNounce.objects.create(service_instance=service_instance, nonce=nonce)
        except Exception:
            return False, "replay"

        # current service token (current kid)
        cur_kid, token_bytes = self.get_active_kid_and_token(service)

        # client instance key (NB: "client:")
        client_key = new(
            token_bytes,
            ("client:" + str(service_instance.instance_id)).encode(),
            sha256,
        ).digest()
        msg = (f"{method}\n{path_q}\n{ts}\n{nonce}\n").encode() + body
        exp = "sha256=" + new(client_key, msg, sha256).hexdigest()

        ok = compare_digest(exp, sig)

        # optional: accept previous kid during rotation
        if not ok and kid and kid != cur_kid:
            prev = self.secrets.get(service)
            if prev is None:
                return False, "unknown service"
            token2 = prev["token"]
            token_bytes2: bytes = b""
            if token2.startswith("base64:"):
                token_bytes2 = b64decode(token2.split(":", 1)[1])
            else:
                token_bytes2 = token2.encode()
            if prev:
                prev_key = new(
                    token_bytes2,
                    ("client:" + str(service_instance.instance_id)).encode(),
                    sha256,
                ).digest()
                exp2 = "sha256=" + new(prev_key, msg, sha256).hexdigest()
                ok = compare_digest(exp2, sig)

        return ok, "ok" if ok else "bad signature"
