"""
Chrome DevTools Protocol (CDP) session extraction.

Connects to a Chrome instance running with ``--remote-debugging-port``
and extracts localStorage / cookies from a matching tab via WebSocket.

This is the primary approach on Windows and serves as a cross-platform
fallback when AppleScript is not available.
"""

import json
from urllib.parse import urlparse

import httpx
import websockets.sync.client as ws_sync
from work_tools.core.exception import TokenRetrievalError
from work_tools.modules.browser.cookies_db import collect_cookies_from_db
from work_tools.modules.browser.schema import SessionInfo

DEFAULT_CDP_PORT = 9222


def _find_tab(port: int, target_domain: str) -> dict:
    """Find the first Chrome tab whose URL contains *target_domain*."""
    try:
        resp = httpx.get(f"http://localhost:{port}/json", timeout=5.0)
        resp.raise_for_status()
    except httpx.ConnectError as e:
        raise TokenRetrievalError(
            f"Could not connect to Chrome DevTools on port {port}.\n"
            "Make sure Chrome is running with: --remote-debugging-port={port}\n\n"
            "  You can start it with:  wt browser chrome-start"
        ) from e
    except Exception as e:
        raise TokenRetrievalError(f"Failed to query Chrome DevTools: {e}") from e

    tabs = resp.json()
    for tab in tabs:
        if tab.get("type") != "page":
            continue
        url = tab.get("url", "")
        if target_domain in url:
            ws_url = tab.get("webSocketDebuggerUrl")
            if not ws_url:
                raise TokenRetrievalError(
                    f"Found a tab matching '{target_domain}' but it has no webSocketDebuggerUrl.\n"
                    "Another DevTools client may already be connected to this tab."
                )
            return tab

    raise TokenRetrievalError(
        f"Could not find a tab with domain '{target_domain}' in Chrome (port {port}).\n"
        "Please make sure you are logged in on that tab in Chrome."
    )


def _evaluate_js(ws_url: str, expression: str) -> str:
    """Execute JavaScript in a Chrome tab via CDP and return the string result."""
    msg = json.dumps(
        {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
            },
        }
    )

    with ws_sync.connect(ws_url) as websocket:
        websocket.send(msg)
        response = json.loads(websocket.recv(timeout=10))

    result = response.get("result", {}).get("result", {})
    if result.get("type") == "string":
        return result["value"]

    # If the result is an object with value, serialize it
    value = result.get("value")
    if value is not None:
        return json.dumps(value) if isinstance(value, (dict, list)) else str(value)

    raise TokenRetrievalError(f"CDP JavaScript evaluation returned unexpected result: {response}")


def get_session_info_cdp(
    target_domain: str,
    local_storage_fields: list[str] | None = None,
    cookie_fields: list[str] | None = None,
    cookie_prefixes: list[str] | None = None,
    port: int = DEFAULT_CDP_PORT,
) -> SessionInfo:
    """Extract localStorage and cookies from a Chrome tab via CDP.

    Requires Chrome to be running with ``--remote-debugging-port=<port>``.

    Args:
        target_domain: Domain string to match against open Chrome tab URLs.
        local_storage_fields: List of localStorage keys to retrieve.
        cookie_fields: List of cookie names to retrieve (exact match).
        cookie_prefixes: List of cookie name prefixes to retrieve.
        port: Chrome DevTools Protocol port (default: 9222).

    Returns:
        SessionInfo object containing the base URL, localStorage values, and cookies.
    """
    needs_cookies = bool(cookie_fields or cookie_prefixes)
    if not local_storage_fields and not needs_cookies:
        raise ValueError("At least one of local_storage_fields, cookie_fields, or cookie_prefixes must be provided.")

    tab = _find_tab(port, target_domain)
    ws_url = tab["webSocketDebuggerUrl"]
    tab_url = tab.get("url", "")

    # ── Build JavaScript (localStorage only) ───────────────────────────
    if local_storage_fields:
        pairs = ", ".join([f'"{f}": localStorage.getItem("{f}")' for f in local_storage_fields])
        ls_js = f"var ls = {{{pairs}}};"
    else:
        ls_js = "var ls = {};"

    js_snippet = f"{ls_js} JSON.stringify({{ls: ls}});"

    # ── Execute and parse ───────────────────────────────────────────────
    try:
        raw = _evaluate_js(ws_url, js_snippet)
        data = json.loads(raw)
    except TokenRetrievalError:
        raise
    except Exception as e:
        raise TokenRetrievalError(f"Unexpected error while extracting Chrome session info via CDP: {e}") from e

    # Determine base_url from tab_url
    parsed = urlparse(tab_url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc
    base_url = f"{scheme}://{netloc}"

    session_info = SessionInfo(base_url=base_url, tab_url=tab_url)
    if local_storage_fields:
        session_info.local_storage = {
            k: (v.strip('"') if isinstance(v, str) else v) for k, v in data.get("ls", {}).items()
        }

    # ── Collect cookies via browser_cookie3 (includes HttpOnly) ─────────
    if needs_cookies:
        session_info.cookies = collect_cookies_from_db(
            domain=netloc,
            cookie_fields=cookie_fields,
            cookie_prefixes=cookie_prefixes,
        )

    return session_info
