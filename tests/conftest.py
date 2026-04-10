import pytest

from modules.taiga.handler import TaigaCLIHandlers
from tests.fake.taiga_client import FakeTaigaClient


@pytest.fixture
def fake_taiga_client():
    """Standalone FakeTaigaClient instance."""
    return FakeTaigaClient()


@pytest.fixture
def taiga_handlers(fake_taiga_client):
    """TaigaCLIHandlers with FakeTaigaClient injected (bypasses browser/HTTP)."""
    handler = TaigaCLIHandlers.__new__(TaigaCLIHandlers)
    handler.client = fake_taiga_client
    return handler


# =============================================================================
# Import Fixtures
# =============================================================================
from .fixtures import *
