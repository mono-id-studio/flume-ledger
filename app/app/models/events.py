from app.models.default.base_model import BaseModel
from django.db.models import (
    CharField,
    PositiveIntegerField,
    JSONField,
    TextField,
    ForeignKey,
    UniqueConstraint,
    Index,
    CASCADE,
    UUIDField,
    BooleanField,
)
from uuid import uuid4
from app.models.services import Service


class EventDefinition(BaseModel):
    """
    Definition of an event published by a Service (publisher).
    Versioning: major separates breaking changes; version_hash for compatible diffs.
    """

    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    publisher = ForeignKey(Service, on_delete=CASCADE, related_name="events")
    event_key = CharField(max_length=200, db_index=True)  # es: "order.created"
    major = PositiveIntegerField()
    display_name = CharField(max_length=200, null=True, blank=True)
    ordering_key_field = CharField(max_length=120, null=True, blank=True)
    delivery_modes = JSONField(default=list)  # es: ["POST_JSON"]
    payload_schema = JSONField()  # JSON Schema
    retention = JSONField(null=True, blank=True)  # es: {"policy":"days","value":7}
    notes = TextField(null=True, blank=True)
    attachments_policy = JSONField(null=True, blank=True)
    version_hash = CharField(max_length=64, db_index=True)  # sha256 esadecimale

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["publisher", "event_key", "major"],
                name="uniq_event_per_publisher_major",
            )
        ]

    def __str__(self):
        return f"{self.publisher.name}:{self.event_key}@v{self.major}"


class Subscription(BaseModel):
    """
    Subscription of a Service (subscriber) to an EventDefinition.
    """

    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    event = ForeignKey(EventDefinition, on_delete=CASCADE, related_name="subscriptions")
    subscriber = ForeignKey(Service, on_delete=CASCADE, related_name="subscriptions")
    webhook_url = CharField(max_length=255)
    # For security: do not save secret in clear. Two alternatives:
    # - secret_ref: reference to vault/secret store; or
    # - secret_hash: hash HMAC/keccak of the secret for audit (without being able to reconstruct it).
    secret_ref = CharField(max_length=255, null=True, blank=True)
    secret_hash = CharField(max_length=128, null=True, blank=True)

    filters = JSONField(default=dict)  # es: {"country":["IT","DE"]}
    dead_letter = JSONField(
        null=True, blank=True
    )  # es: {"url":"...","max_attempts":12}
    enabled = BooleanField(default=True)

    class Meta:
        constraints = [
            # one subscription per subscriber on (publisher,event_key,major)
            UniqueConstraint(
                fields=["event", "subscriber"],
                name="uniq_subscription_event_subscriber",
            )
        ]
        indexes = [
            Index(fields=["subscriber"]),
            Index(fields=["enabled"]),
        ]

    def __str__(self):
        return f"{self.subscriber.name} -> {self.event}"
