from django.db.models import F, IntegerField, BigIntegerField
from django.db.transaction import atomic
from app.models.default.base_model import BaseModel


class RegistryState(BaseModel):
    """
    Global version for the distributed registry.
    Keep ONE row (pk fixed = 1). Increment on relevant mutations.
    """

    pkid = IntegerField(primary_key=True, default=1, editable=False)
    registry_version = BigIntegerField(default=0)

    @classmethod
    @atomic
    def bump(cls) -> int:
        """
        Atomically increments and returns the new version.
        Locks the single row so multiple ledger replicas don't race.
        """
        obj, _ = cls.objects.select_for_update().get_or_create(pkid=1)
        obj.registry_version = F("registry_version") + 1
        obj.save(update_fields=["registry_version"])
        obj.refresh_from_db(fields=["registry_version"])  # resolve F()
        return obj.registry_version

    @classmethod
    def current(cls) -> int:
        try:
            return cls.objects.only("registry_version").get(pkid=1).registry_version
        except cls.DoesNotExist:
            return 0

    @classmethod
    @atomic
    def maybe_bump(cls, changed: bool) -> int:
        """
        Bump only if 'changed' is True, otherwise return current.
        Useful to keep logic tidy in endpoints.
        """
        if changed:
            return cls.bump()
        return cls.current()
