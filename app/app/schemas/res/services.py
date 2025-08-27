from typing import List, Annotated
from ninja import Schema, Field


class RegisterResponse(Schema):
    service_id: Annotated[
        str,
        Field(
            description="The ID of the service",
            title="Service ID",
            example="123e4567-e89b-12d3-a456-426614174000",
        ),
    ]
    instance_id: Annotated[
        str,
        Field(
            description="The ID of the instance",
            title="Instance ID",
            example="123e4567-e89b-12d3-a456-426614174000",
        ),
    ]
    push_kid: Annotated[
        str,
        Field(
            description="The push key ID",
            title="Push Key ID",
            example="v1",
        ),
    ]
    lease_ttl_sec: Annotated[
        int,
        Field(
            description="The lease TTL in seconds",
            title="Lease TTL",
            example=300,
        ),
    ]
    registry_version: Annotated[
        int,
        Field(
            description="The registry version",
            title="Registry Version",
            example=1,
        ),
    ]


class ServiceInstanceSnapshot(Schema):
    instance_id: Annotated[
        str,
        Field(
            description="The ID of the instance",
            title="Instance ID",
            example="123e4567-e89b-12d3-a456-426614174000",
        ),
    ]
    base_url: Annotated[
        str,
        Field(
            description="The base URL of the instance",
            title="Base URL",
            example="http://127.0.0.1:8080",
        ),
    ]
    status: Annotated[
        str,
        Field(description="The status of the instance", title="Status", example="UP"),
    ]
    meta: Annotated[
        dict,
        Field(
            description="The metadata of the instance",
            title="Metadata",
            example={"zone": "eu-central-1"},
        ),
    ]


class Capabilities(Schema):
    publishes: Annotated[
        List[str],
        Field(
            description="The publishes of the instance",
            title="Publishes",
            example=["order.created", "invoice.issued"],
        ),
    ]
    consumes: Annotated[
        List[str],
        Field(
            description="The consumes of the instance",
            title="Consumes",
            example=["customer.updated"],
        ),
    ]


class ServiceSnapshot(Schema):
    service_id: Annotated[
        str,
        Field(
            description="The ID of the service",
            title="Service ID",
            example="123e4567-e89b-12d3-a456-426614174000",
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="The name of the service",
            title="Service Name",
            example="billing",
        ),
    ]
    capabilities: Capabilities
    meta: Annotated[
        dict,
        Field(
            description="The metadata of the service",
            title="Metadata",
            example={"owner": "team-foo"},
        ),
    ]
    instances: Annotated[
        list[ServiceInstanceSnapshot],
        Field(
            description="The instances of the service",
            title="Instances",
        ),
    ]


class ServiceSnapshotResponse(Schema):
    version: Annotated[
        int,
        Field(
            description="The version of the service snapshot",
            title="Version",
            example=1,
        ),
    ]
    services: Annotated[
        list[ServiceSnapshot],
        Field(description="The services of the service snapshot", title="Services"),
    ]
