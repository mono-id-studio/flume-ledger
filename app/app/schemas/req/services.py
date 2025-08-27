from typing import Optional, List, Annotated
from ninja import Schema, Field
from pydantic import AnyHttpUrl


# ---- nested ----


class RegisterRequestCapabilities(Schema):
    publishes: Annotated[
        List[str],
        Field(
            description="Events published by the service",
            examples=["user.created", "user.updated"],
        ),
    ] = []
    consumes: Annotated[
        List[str],
        Field(
            description="Events consumed by the service",
            examples=["user.created", "user.updated"],
        ),
    ] = []


class RegisterRequestMeta(Schema):
    zone: Annotated[
        Optional[str],
        Field(description="Zone of the node", examples=["z1", "eu-central-1a"]),
    ] = None  # es: "z1" / "eu-central-1a"
    weight: Annotated[
        Optional[int], Field(description="For client-side balancing", examples=[1, 2])
    ] = None


# ---- top level ----


class RegisterRequest(Schema):
    # logical service name (not the replica)
    service_name: Annotated[
        str,
        Field(
            description="Logical service name (not the replica)",
            examples=["user-service", "order-service"],
        ),
    ]
    # where the instance listens in the internal network
    base_url: Annotated[
        AnyHttpUrl,
        Field(
            description="Where the instance listens in the internal network",
            examples=["http://10.0.1.11:8080", "http://10.0.1.12:8080"],
        ),
    ]  # es: http://10.0.1.11:8080
    # optional but recommended for heartbeat out of band
    health_url: Annotated[
        Optional[AnyHttpUrl],
        Field(
            description="Optional but recommended for heartbeat out of band",
            examples=["http://10.0.1.11:8080/health", "http://10.0.1.12:8080/health"],
        ),
    ] = None
    # how often the client beats (the ledger will calculate TTL and M miss)
    heartbeat_interval_sec: Annotated[
        int,
        Field(
            description="How often the client beats (the ledger will calculate TTL and M miss)",
            examples=[10, 20],
        ),
    ] = 10
    capabilities: Annotated[
        Optional[RegisterRequestCapabilities],
        Field(
            description="Capabilities of the service",
            examples=[
                {
                    "publishes": ["user.created", "user.updated"],
                    "consumes": ["user.created", "user.updated"],
                }
            ],
        ),
    ] = None
    meta: Annotated[
        Optional[RegisterRequestMeta],
        Field(
            description="Meta information about the service",
            examples=[
                {
                    "zone": "z1",
                    "node_id": "node-1",
                    "task_slots": 1,
                    "boot_id": "boot-1",
                    "weight": 1,
                }
            ],
        ),
    ] = None
    bootstrap_secret_ref: Annotated[
        str, Field(examples=["bootstrap-secret-1", "bootstrap-secret-2"])
    ]
    boot_id: Annotated[str, Field(examples=["boot-1", "boot-2"])]
    node_id: Annotated[str, Field(examples=["node-1", "node-2"])]
    task_slot: Annotated[int, Field(examples=[1, 2])]
