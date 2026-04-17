"""Unit tests for SlackClient using a mock WebClient."""

from unittest.mock import MagicMock

import pytest
from work_tools.modules.slack.client import SlackClient
from work_tools.modules.slack.config import SlackSettings


@pytest.fixture
def mock_web_client():
    return MagicMock()


@pytest.fixture
def slack_settings():
    return SlackSettings(SLACK_BOT_TOKEN="xoxb-test", SLACK_DEFAULT_CHANNEL="C_TEST")


@pytest.fixture
def slack_client(slack_settings, mock_web_client):
    return SlackClient(settings=slack_settings, web_client=mock_web_client)


class TestSlackClient:
    def test_post_message_success(self, slack_client, mock_web_client):
        mock_web_client.chat_postMessage.return_value.data = {"ok": True, "ts": "123.456"}

        response = slack_client.post_message("hello", channel="C123")

        assert response["ok"] is True
        assert response["ts"] == "123.456"
        mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C123",
            text="hello",
            unfurl_links=False,
            unfurl_media=False,
        )

    def test_post_message_default_channel(self, slack_client, mock_web_client):
        mock_web_client.chat_postMessage.return_value.data = {"ok": True}

        slack_client.post_message("hello")

        mock_web_client.chat_postMessage.assert_called_once()
        args, kwargs = mock_web_client.chat_postMessage.call_args
        assert kwargs["channel"] == "C_TEST"

    def test_post_snippet_success(self, slack_client, mock_web_client):
        mock_web_client.files_upload_v2.return_value.data = {"ok": True, "file": {"id": "F123"}}

        response = slack_client.post_snippet("some content", title="Snippet Title")

        assert response["ok"] is True
        mock_web_client.files_upload_v2.assert_called_once_with(
            channels="C_TEST",
            content="some content",
            filename="snippet.txt",
            filetype="text",
            title="Snippet Title",
        )

    def test_resolve_channel_id_found(self, slack_client, mock_web_client):
        mock_web_client.conversations_list.return_value.data = {
            "ok": True,
            "channels": [{"name": "general", "id": "C_GENERAL"}, {"name": "random", "id": "C_RANDOM"}],
            "response_metadata": {"next_cursor": ""},
        }

        channel_id = slack_client.resolve_channel_id("random")

        assert channel_id == "C_RANDOM"
        mock_web_client.conversations_list.assert_called_once()

    def test_resolve_channel_id_not_found(self, slack_client, mock_web_client):
        mock_web_client.conversations_list.return_value.data = {
            "ok": True,
            "channels": [{"name": "general", "id": "C_GENERAL"}],
            "response_metadata": {"next_cursor": ""},
        }

        channel_id = slack_client.resolve_channel_id("nonexistent")

        assert channel_id is None

    def test_resolve_channel_id_pagination(self, slack_client, mock_web_client):
        # First page has next_cursor
        mock_web_client.conversations_list.side_effect = [
            MagicMock(
                data={
                    "ok": True,
                    "channels": [{"name": "page1", "id": "C1"}],
                    "response_metadata": {"next_cursor": "cursor-2"},
                }
            ),
            MagicMock(
                data={
                    "ok": True,
                    "channels": [{"name": "page2", "id": "C2"}],
                    "response_metadata": {"next_cursor": ""},
                }
            ),
        ]

        channel_id = slack_client.resolve_channel_id("page2")

        assert channel_id == "C2"
        assert mock_web_client.conversations_list.call_count == 2
