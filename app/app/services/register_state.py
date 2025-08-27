from app.models.register import RegistryState


class RegistryStateService:
    def maybe_bump(self, changed: bool) -> int:
        return RegistryState.maybe_bump(changed)
