# app/models/ledger.py
from django.db.models import (
    UUIDField,
    CharField,
    JSONField,
    ForeignKey,
    CASCADE,
    Index,
    TextChoices,
    UniqueConstraint,
    Q,
)
from django.db.models import IntegerField, DateTimeField
from uuid import uuid4
from app.models.default.base_model import BaseModel


class Service(BaseModel):
    """
    A logical service (e.g. 'billing'). Has 0..N instances.
    """

    service_id = UUIDField(primary_key=True, default=uuid4, editable=False)
    name = CharField(max_length=120, unique=True, db_index=True)
    # opzionale: capabilities dichiarate a livello servizio (non istanza)
    publishes = JSONField(default=list)  # es: ["order.created", "invoice.issued"]
    consumes = JSONField(default=list)  # es: ["customer.updated"]
    meta = JSONField(default=dict)  # es: {"owner":"team-foo"}
    region = CharField(max_length=120, default="eu-central-1")
    ttl_s = IntegerField(default=300)

    bootstrap_secret_ref = CharField(max_length=255)
    # For audit: hash of the token (to know if it has changed) – NOT the token in clear
    bootstrap_token_hash = CharField(max_length=128, blank=True)
    # Current key ID used to derive the push signatures (useful for rotations)
    active_kid = CharField(max_length=32, default="v1")

    def __str__(self):
        return self.name


class ServiceInstance(BaseModel):
    class Status(TextChoices):
        UP = "UP"
        DOWN = "DOWN"
        DRAIN = "DRAIN"

    # stable PK assigned by the ledger
    instance_id = UUIDField(primary_key=True, default=uuid4, editable=False)

    service = ForeignKey(Service, on_delete=CASCADE, related_name="instances")

    # logical key for dedup (restarts/moves)
    node_id = CharField(max_length=64, null=True, blank=True)  # es. {{.Node.ID}}
    task_slot = IntegerField(null=True, blank=True)  # es. {{.Task.Slot}}
    boot_id = CharField(max_length=64, null=True, blank=True)  # es. {{.Boot.ID}}

    # Volatile data (can change on every register)
    base_url = CharField(max_length=255)
    health_url = CharField(max_length=255)
    heartbeat_interval_sec = IntegerField(default=10)

    status = CharField(max_length=10, choices=Status.choices, default=Status.UP)
    last_heartbeat_at = DateTimeField(null=True, blank=True)
    consecutive_miss = IntegerField(default=0)

    push_kid = CharField(max_length=32, default="v1")

    # Other metadata (zone, weight, boot_id, etc.)
    meta = JSONField(default=dict)

    class Meta:
        indexes = [
            Index(fields=["service", "status"]),
            Index(fields=["last_heartbeat_at"]),
            Index(
                fields=["service", "node_id", "task_slot"]
            ),  # fast lookup on the register
        ]
        constraints = [
            # Unique per (service, node_id, task_slot) when both are set
            UniqueConstraint(
                fields=["service", "node_id", "task_slot"],
                name="uniq_instance_by_service_node_slot",
                condition=Q(node_id__isnull=False, task_slot__isnull=False),
            ),
        ]

    def __str__(self):
        return f"{self.service.name}@{self.base_url}"


class InboundNounce(BaseModel):
    service_instance = ForeignKey(
        ServiceInstance, on_delete=CASCADE, related_name="nonces"
    )
    nonce = CharField(max_length=64, db_index=True)

    class Meta:
        unique_together = ("service_instance", "nonce")
