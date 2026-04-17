"""
browser
-------
Handles browser session integration.
Extracts authentication tokens and cookies from a running browser (e.g. Chrome)
to enable authenticated API calls without manual login.

Supports two backends:
- **AppleScript** (macOS default) — no extra setup needed.
- **CDP** (Windows/Linux) — requires Chrome started with ``--remote-debugging-port``.
"""

from .api import cli
from .client import AuthMode, BrowserTokenBaseClient
from .schema import SessionInfo
from .session import get_session_info

__all__ = [
    "AuthMode",
    "BrowserTokenBaseClient",
    "SessionInfo",
    "cli",
    "get_session_info",
]
