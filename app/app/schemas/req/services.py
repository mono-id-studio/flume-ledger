from typing import Annotated, Optional, List
from ninja import Schema
from pydantic import AnyHttpUrl


# ---- nested ----


class RegisterRequestCapabilities(Schema):
    publishes: List[str] = []
    consumes: List[str] = []


class RegisterRequestMeta(Schema):
    zone: Optional[str] = None  # es: "z1" / "eu-central-1a"
    node_id: Optional[str] = None  # stable identifier of the node
    task_slots: Optional[int] = None  # number of tasks the node can run
    boot_id: Optional[str] = None  # changes on every reboot
    weight: Optional[int] = None  # for client-side balancing


class RegisterRequest(Schema):
    # logical service name (not the replica)
    service_name: str
    # where the instance listens in the internal network
    base_url: AnyHttpUrl  # es: http://10.0.1.11:8080
    # optional but recommended for heartbeat out of band
    health_url: Optional[AnyHttpUrl] = None
    # how often the client beats (the ledger will calculate TTL and M miss)
    heartbeat_interval_sec: int = 10
    capabilities: Optional[RegisterRequestCapabilities] = None
    meta: Optional[RegisterRequestMeta] = None
    bootstrap_secret_ref: str
    boot_id: str
    node_id: str
    task_slot: int
