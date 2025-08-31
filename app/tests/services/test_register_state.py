import pytest
from app.services.register_state import RegistryStateService


@pytest.mark.django_db
def test_register_state_service_maybe_bump():
    assert RegistryStateService().maybe_bump(True) == 1
    assert RegistryStateService().maybe_bump(False) == 1
    assert RegistryStateService().maybe_bump(True) == 2
