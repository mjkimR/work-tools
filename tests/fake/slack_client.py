"""FakeSlackClient — drop-in replacement for SlackClient without real Slack API calls.

Matches SlackClient's public method signatures exactly.
If a signature changes, tests using this fake will break → interface drift detected.

Call recordings
---------------
All sent messages/snippets are stored in public lists so that tests can assert
on *what* was sent without any HTTP traffic:

    fake.messages          — records from post_message()
    fake.snippets          — records from post_snippet()
    fake.channel_registry  — name→id mapping used by resolve_channel_id()
"""

from __future__ import annotations


class FakeSlackClient:
    """Fake that replaces SlackClient for handler-level testing.

    Bypasses Slack API entirely. Returns minimal response payloads that
    mirror the shape of real Slack responses so that callers can use
    ``response["ts"]``, ``response["ok"]``, etc. without error.
    """

    def __init__(self, default_channel: str = "C_DEFAULT"):
        self._default_channel = default_channel

        # Call recordings for assertions
        self.messages: list[dict] = []
        self.snippets: list[dict] = []

        # Seed with a couple of channels; tests can extend this
        self.channel_registry: dict[str, str] = {
            "general": "C_GENERAL",
            "random": "C_RANDOM",
        }

        # Auto-incrementing timestamp counter
        self._ts_counter = 1000000000

    # ── Internal helpers ─────────────────────────────────────────────────

    def _next_ts(self) -> str:
        self._ts_counter += 1
        return f"{self._ts_counter}.000000"

    def _resolve(self, channel: str | None) -> str:
        ch = channel or self._default_channel
        if not ch:
            raise ValueError("No channel specified. Pass a channel argument or set SLACK_DEFAULT_CHANNEL.")
        return ch

    # ── API methods (same signatures as SlackClient) ─────────────────────

    def post_message(
        self,
        text: str,
        channel: str | None = None,
        *,
        blocks: list[dict] | None = None,
        thread_ts: str | None = None,
        unfurl_links: bool = False,
    ) -> dict:
        """Record a message post and return a minimal Slack-shaped response."""
        ts = self._next_ts()
        record = {
            "channel": self._resolve(channel),
            "text": text,
            "blocks": blocks,
            "thread_ts": thread_ts,
            "unfurl_links": unfurl_links,
            "ts": ts,
        }
        self.messages.append(record)
        return {"ok": True, "ts": ts, "channel": record["channel"]}

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
        """Record a snippet upload and return a minimal Slack-shaped response."""
        record = {
            "channel": self._resolve(channel),
            "content": content,
            "title": title,
            "filename": filename,
            "filetype": filetype,
            "thread_ts": thread_ts,
        }
        self.snippets.append(record)
        return {"ok": True, "file": {"id": f"F{len(self.snippets):04d}", "title": title}}

    def resolve_channel_id(self, name: str) -> str | None:
        """Look up channel ID from the in-memory registry."""
        return self.channel_registry.get(name)
