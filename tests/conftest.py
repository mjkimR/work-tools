import pytest
from modules.taiga.handler import TaigaCLIHandlers

from tests.fake.data.ims import LOGIN_REQUIRED_HTML, SAMPLE_DOCUMENT_HTML
from tests.fake.ims_client import FakeImsClient
from tests.fake.taiga_client import FakeTaigaClient
from tests.utils.git_repo import make_git_repo

# =============================================================================
# Taiga
# =============================================================================


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
# IMS
# =============================================================================


@pytest.fixture
def fake_ims_client():
    """Standalone FakeImsClient instance."""
    return FakeImsClient()


@pytest.fixture
def sample_document_html():
    """Sample KBoard document HTML for parser tests."""
    return SAMPLE_DOCUMENT_HTML


@pytest.fixture
def login_required_html():
    """HTML page without kboard-document-wrap (login-required simulation)."""
    return LOGIN_REQUIRED_HTML


# =============================================================================
# Git Repo
# =============================================================================


@pytest.fixture
def git_manager(tmp_path, monkeypatch):
    """GitRepoManager backed by a real temporary git repo with sample commits."""
    monkeypatch.setenv("GIT_USER_EMAIL", "test@example.com")
    monkeypatch.setenv("GIT_TARGET_REPO", str(tmp_path))
    return make_git_repo(tmp_path)
