from typing import Mapping, Tuple
from app.models.services import (
    Service,
    ServiceInstance,
    InboundNonceBootstrap,
    InboundServiceInstanceNonce,
)
from app.services.secrets import SecretsServiceProtocol
from time import time
from os import urandom
from hmac import new, compare_digest
from hashlib import sha256
from typing import Protocol
from django.db import IntegrityError
from app.common.default.security import token_to_bytes
from datetime import datetime


class SignerServiceProtocol(Protocol):
    def signed_headers_for(
        self,
        instance: ServiceInstance,
        method: str,
        path_with_query: str,
        body: bytes = b"",
    ) -> Mapping[str, str]: ...

    def get_active_kid_and_token(self, service: Service) -> Tuple[str, bytes]: ...

    def derive_instance_key(
        self, scope: str, token_bytes: bytes, instance_id: str
    ) -> bytes: ...

    def _verify_ts_window(self, ts: int, ts_window: int = 300) -> bool: ...

    def bootstrap_verification(
        self,
        service_name: str,
        token: str,
        ts: int,
        nonce: str,
        signature: str,
        body: bytes = b"",
        ts_window: int = 60,
    ) -> tuple[bool, str]: ...

    def instance_verification(
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
    secrets: type[SecretsServiceProtocol]

    def __init__(self, secrets: type[SecretsServiceProtocol]):
        self.secrets = secrets

    def signed_headers_for(
        self,
        instance: ServiceInstance,
        method: str,
        path_with_query: str,
        body: bytes = b"",
    ) -> Mapping[str, str]:
        service = instance.service
        kid, token_bytes = self.get_active_kid_and_token(service)

        ts = int(time())
        nonce = urandom(16).hex()
        key = self.derive_instance_key("push", token_bytes, str(instance.instance_id))
        msg = (f"{method.upper()}\n{path_with_query}\n{ts}\n{nonce}\n").encode() + (
            body or b""
        )
        sig = new(key, msg, sha256).hexdigest()

        return {
            "X-Timestamp": str(ts),
            "X-Nonce": nonce,
            "X-Signature": f"sha256={sig}",
            "X-Key-Id": kid,
            "X-Signed-Method": method.upper(),
            "X-Signed-Path-With-Query": path_with_query,
            "Content-Type": "application/json",
        }

    def get_active_kid_and_token(self, service: Service) -> Tuple[str, bytes]:
        data = self.secrets.get_current(service)
        if data is None:
            raise ValueError("No secrets found for service")
        return data

    def derive_instance_key(
        self, scope: str, token_bytes: bytes, instance_id: str
    ) -> bytes:
        return new(token_bytes, (scope + ":" + instance_id).encode(), sha256).digest()

    def _verify_ts_window(self, ts: int, ts_window: int = 300) -> bool:
        return abs(time() - ts) <= ts_window

    def instance_verification(
        self,
        service: Service,
        ts: int,
        nonce: str,
        signature: str,  # atteso: "sha256=<hex>"
        kid: str,  # OBBLIGATORIO (strict)
        service_instance: ServiceInstance,
        body: bytes = b"",
        method: str = "GET",
        path_q: str = "",
        ts_window: int = 300,
    ) -> tuple[bool, str]:
        # 0) sanity
        if not (isinstance(ts, int)):
            return False, "missing timestamp"
        if not nonce:
            return False, "missing nonce"
        if not kid:
            return False, "missing kid"

        # 1) timestamp window
        if not self._verify_ts_window(ts, ts_window):
            return False, "timestamp window"

        # 2) anti-replay per istanza
        try:
            InboundServiceInstanceNonce.objects.create(
                service_instance=service_instance, nonce=nonce
            )
        except IntegrityError:
            return False, "replay"

        # 3) formato firma: "sha256=<hex>"
        if not (
            isinstance(signature, str)
            and signature[:7].lower() == "sha256="
            and len(signature) > 7
        ):
            return False, "bad signature format"
        sig_hex = signature[7:].lower()

        # 4) messaggio firmato
        m = (method or "GET").upper()
        p = path_q or "/"
        if not (m and p):
            return False, "missing method or path"
        msg = (f"{m}\n{p}\n{ts}\n{nonce}\n").encode() + (body or b"")

        # 5) chiavi current/prev
        cur = self.secrets.get_current(service)
        if not cur:
            return False, "no current secret"
        cur_kid, cur_token_bytes = cur
        prev = self.secrets.get_previous(service)  # (prev_kid, prev_bytes) | None

        instance_id_str = str(service_instance.instance_id)

        # 6) selezione chiave in base al KID
        if kid == cur_kid:
            key_bytes = self.derive_instance_key(
                "client", cur_token_bytes, instance_id_str
            )
        elif prev and kid == prev[0]:
            so = self.secrets.get(service)  # SecretObject (cached)
            if so and so.accept_prev_until and datetime.now() > so.accept_prev_until:
                return False, "prev key expired"
            key_bytes = self.derive_instance_key("client", prev[1], instance_id_str)
        else:
            return False, "unknown kid"

        # 7) verifica HMAC
        exp_hex = new(key_bytes, msg, sha256).hexdigest()
        if compare_digest(exp_hex, sig_hex):
            return True, "ok"
        return False, "bad signature"

    def bootstrap_verification(
        self,
        service_name: str,
        token: str,
        ts: int,
        nonce: str,
        signature: str,  # "sha256=<hex>"
        body: bytes = b"",
        ts_window: int = 60,
    ) -> tuple[bool, str]:
        # 1) timestamp (int) e finestra
        if not (isinstance(ts, int)):
            return False, "missing timestamp"
        if not self._verify_ts_window(ts, ts_window):
            return False, "timestamp window"

        # 2) anti-replay per service_name
        if not nonce:
            return False, "missing nonce"
        try:
            InboundNonceBootstrap.objects.create(service_name=service_name, nonce=nonce)
        except IntegrityError:
            return False, "replay"

        # 3) formato firma: "sha256=<hex>"
        if not (
            isinstance(signature, str)
            and signature[:7].lower() == "sha256="
            and len(signature) > 7
        ):
            return False, "bad signature format"
        sig_hex = signature[7:].lower()

        # 4) HMAC con bootstrap token
        key_bytes = token_to_bytes(token)
        msg = f"{ts}.{nonce}".encode() + (body or b"")
        exp_hex = new(key_bytes, msg, sha256).hexdigest()
        ok = compare_digest(exp_hex, sig_hex)
        return (ok, "ok" if ok else "bad signature")
