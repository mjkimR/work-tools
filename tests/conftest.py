import pytest
from modules.ims.handler import ImsCLIHandlers
from modules.taiga.handler import TaigaCLIHandlers
from modules.workflow.handler.taiga_ims import TaigaImsWorkflowHandler

from tests.fake.data.ims import LOGIN_REQUIRED_HTML, SAMPLE_DOCUMENT_HTML
from tests.fake.data.taiga import (
    CUSTOM_ATTRIBUTE_VALUES_WITH_IMS,
    USER_STORIES_WITH_IMS,
)
from tests.fake.ims_client import FakeImsClient
from tests.fake.slack_client import FakeSlackClient
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
def ims_handlers(fake_ims_client):
    """ImsCLIHandlers with FakeImsClient injected (bypasses browser/HTTP)."""
    handler = ImsCLIHandlers.__new__(ImsCLIHandlers)
    handler.client = fake_ims_client
    return handler


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


# =============================================================================
# Slack
# =============================================================================


@pytest.fixture
def fake_slack_client():
    """Standalone FakeSlackClient instance."""
    return FakeSlackClient()


# =============================================================================
# Workflow (Taiga-IMS)
# =============================================================================


class FakeTaigaClientWithIms(FakeTaigaClient):
    """FakeTaigaClient extended with IMS-linked US data for workflow handler tests."""

    def get_user_story(self, us_id):
        if us_id in USER_STORIES_WITH_IMS:
            return USER_STORIES_WITH_IMS[us_id]
        return super().get_user_story(us_id)

    def get_user_story_by_ref(self, ref):
        # IMS-linked US ref 조회를 우선 시도
        ims_by_ref = {us["ref"]: us for us in USER_STORIES_WITH_IMS.values()}
        if ref in ims_by_ref:
            return ims_by_ref[ref]
        return super().get_user_story_by_ref(ref)

    def get_userstory_custom_attribute_values(self, us_id):
        if us_id in CUSTOM_ATTRIBUTE_VALUES_WITH_IMS:
            return CUSTOM_ATTRIBUTE_VALUES_WITH_IMS[us_id]
        return super().get_userstory_custom_attribute_values(us_id)


@pytest.fixture
def fake_taiga_client_with_ims():
    """FakeTaigaClientWithIms instance for workflow handler tests."""
    return FakeTaigaClientWithIms()


@pytest.fixture
def workflow_handler(fake_taiga_client_with_ims, fake_ims_client):
    """TaigaImsWorkflowHandler with Fake clients injected (bypasses browser/HTTP).

    Pre-registers IMS documents keyed by the UUIDs used in test fixtures so that
    get_document(uuid) calls resolve correctly during workflow handler tests.
    """
    from tests.fake.data.taiga import IMS_UUID_IN_CUSTOM_ATTR, IMS_UUID_IN_DESCRIPTION

    # FakeImsClient의 _documents 키를 UUID로도 등록 (workflow handler는 UUID로 조회함)
    sample_html = fake_ims_client._documents["8226"]
    fake_ims_client.add_document(IMS_UUID_IN_DESCRIPTION, sample_html)
    fake_ims_client.add_document(IMS_UUID_IN_CUSTOM_ATTR, sample_html)

    handler = TaigaImsWorkflowHandler.__new__(TaigaImsWorkflowHandler)
    handler.taiga_client = fake_taiga_client_with_ims
    handler.ims_client = fake_ims_client
    handler.util = fake_ims_client.util
    return handler


@pytest.fixture
def fake_ims_client_with_two_docs(fake_taiga_client_with_ims, fake_ims_client):
    """workflow_handler whose FakeImsClient has an extra document registered for uuid=aaaa-1111-bbbb-2222."""
    fake_ims_client.add_document("8226_extra", fake_ims_client._documents["8226"])
    handler = TaigaImsWorkflowHandler.__new__(TaigaImsWorkflowHandler)
    handler.taiga_client = fake_taiga_client_with_ims
    handler.ims_client = fake_ims_client
    handler.util = fake_ims_client.util
    return handler
