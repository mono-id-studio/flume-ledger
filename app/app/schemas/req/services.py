from typing import Optional, List
from uuid import UUID
from ninja import Schema
from pydantic import AnyHttpUrl, constr, conint


# ---- nested ----


class RegisterRequestCapabilities(Schema):
    publishes: List[str] = []
    consumes: List[str] = []


class RegisterRequestMeta(Schema):
    zone: Optional[str] = None  # es: "z1" / "eu-central-1a"
    node_id: Optional[str] = None  # stable identifier of the node
    task_slots: Optional[int] = None  # number of tasks the node can run
    boot_id: Optional[str] = None  # changes on every reboot
    weight: conint(ge=1, le=100) = 1  # for client-side balancing


# ---- request ----


class RegisterRequest(Schema):
    # logical service name (not the replica)
    service_name: constr(
        strip_whitespace=True, min_length=1, regex=r"^[a-z][a-z0-9-_]{1,63}$"
    )
    # where the instance listens in the internal network
    base_url: AnyHttpUrl  # es: http://10.0.1.11:8080
    # optional but recommended for heartbeat out of band
    health_url: Optional[AnyHttpUrl] = None
    # how often the client beats (the ledger will calculate TTL and M miss)
    heartbeat_interval_sec: conint(ge=1, le=3600) = 10
    capabilities: Optional[RegisterRequestCapabilities] = None
    meta: Optional[RegisterRequestMeta] = None
    # NB: no instance_id here – the ledger generates it
