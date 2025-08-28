from app.models.register import RegistryState
from typing import Protocol


class RegistryStateServiceProtocol(Protocol):
    def maybe_bump(self, changed: bool) -> int: ...


class RegistryStateService:
    def maybe_bump(self, changed: bool) -> int:
        return RegistryState.maybe_bump(changed)
