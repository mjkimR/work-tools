"""Slack API client backed by slack-sdk WebClient.

Authentication
--------------
Bot Token (``xoxb-...``) stored in ``SLACK_BOT_TOKEN`` environment variable.
Unlike Taiga/IMS, Slack does not require browser-session discovery.

Scopes required
---------------
- ``chat:write``          — post messages
- ``chat:write.public``   — post to channels the bot hasn't joined
- ``files:write``         — upload files / snippets
- ``channels:read``       — resolve channel names → IDs
"""

from __future__ import annotations

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError  # re-exported for callers  # noqa: F401
from work_tools.modules.slack.config import SlackSettings, get_slack_settings


class SlackClient:
    """Thin wrapper around ``slack_sdk.WebClient``.

    Provides helpers for the operations this project actually needs:
    posting plain-text or block messages, uploading text snippets,
    and resolving channel names.

    Attributes:
        settings: Slack connection settings loaded from environment variables.
        _web: The underlying ``slack_sdk.WebClient`` instance.
    """

    def __init__(self, settings: SlackSettings | None = None, web_client: WebClient | None = None):
        self.settings: SlackSettings = settings or get_slack_settings()
        self._web = web_client or WebClient(token=self.settings.bot_token)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _channel(self, channel: str | None) -> str:
        """Return *channel* if given, else fall back to ``settings.default_channel``.

        Raises:
            ValueError: If neither argument nor default is configured.
        """
        ch = channel or self.settings.default_channel
        if not ch:
            raise ValueError("No channel specified. Pass a channel argument or set SLACK_DEFAULT_CHANNEL.")
        return ch

    # ── API methods ──────────────────────────────────────────────────────

    def post_message(
        self,
        text: str,
        channel: str | None = None,
        *,
        blocks: list[dict] | None = None,
        thread_ts: str | None = None,
        unfurl_links: bool = False,
    ) -> dict:
        """Post a plain-text or Block Kit message to a channel.

        Args:
            text:         Message text (shown in notifications and as fallback for blocks).
            channel:      Channel ID (``C…``) or name (``#general``).
                          Defaults to ``SLACK_DEFAULT_CHANNEL``.
            blocks:       Optional Block Kit block list. When supplied, ``text``
                          acts as the notification fallback only.
            thread_ts:    Timestamp of the parent message to reply in-thread.
            unfurl_links: Whether Slack should unfurl URLs in the message.

        Returns:
            The Slack API response payload (``dict``).

        Raises:
            SlackApiError: On any Slack API error.
        """
        kwargs: dict = {
            "channel": self._channel(channel),
            "text": text,
            "unfurl_links": unfurl_links,
            "unfurl_media": False,
        }
        if blocks:
            kwargs["blocks"] = blocks
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        response = self._web.chat_postMessage(**kwargs)
        return dict(response.data)

    def post_snippet(
        self,
        content: str,
        channel: str | None = None,
        *,
        title: str = "",
        filename: str = "snippet.txt",
        filetype: str = "text",
        thread_ts: str | None = None,
    ) -> dict:
        """Upload a text snippet (file) to a channel.

        Useful for long structured text (e.g. ``str(ImsDocument)``) that
        would be hard to read as a normal chat message.

        Args:
            content:   The text content to upload.
            channel:   Channel ID or name. Defaults to ``SLACK_DEFAULT_CHANNEL``.
            title:     Display title shown above the snippet.
            filename:  Filename hint for the uploaded file.
            filetype:  Slack filetype string (``text``, ``python``, ``markdown``, …).
            thread_ts: Post the snippet as a reply in the given thread.

        Returns:
            The Slack API response payload (``dict``).

        Raises:
            SlackApiError: On any Slack API error.
        """
        kwargs: dict = {
            "channels": self._channel(channel),
            "content": content,
            "filename": filename,
            "filetype": filetype,
        }
        if title:
            kwargs["title"] = title
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        response = self._web.files_upload_v2(**kwargs)
        return dict(response.data)

    def resolve_channel_id(self, name: str) -> str | None:
        """Return the channel ID for *name* (without leading ``#``).

        Paginates through ``conversations.list`` until a match is found.

        Args:
            name: Channel name without ``#`` prefix (e.g. ``"general"``).

        Returns:
            Channel ID string if found, ``None`` otherwise.

        Raises:
            SlackApiError: On any Slack API error.
        """
        cursor: str | None = None
        while True:
            params: dict = {"limit": 200, "exclude_archived": True}
            if cursor:
                params["cursor"] = cursor

            response = self._web.conversations_list(**params)
            data = dict(response.data)

            for ch in data.get("channels", []):
                if ch.get("name") == name:
                    return ch["id"]

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                return None
