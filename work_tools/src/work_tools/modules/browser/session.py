"""
Session extraction from a running Chrome browser.

- **macOS**: Uses AppleScript (default, no extra setup needed).
- **Windows / Linux**: Uses Chrome DevTools Protocol (CDP).
  Requires Chrome to be started with ``--remote-debugging-port=9222``.
"""

import json
import platform
import subprocess
from urllib.parse import urlparse

from work_tools.core.exception import TokenRetrievalError
from work_tools.modules.browser.cookies_db import collect_cookies_from_db
from work_tools.modules.browser.schema import SessionInfo
from work_tools.modules.browser.session_cdp import DEFAULT_CDP_PORT, get_session_info_cdp


def get_session_info(
    target_domain,
    local_storage_fields: list[str] | None = None,
    cookie_fields: list[str] | None = None,
    cookie_prefixes: list[str] | None = None,
    *,
    backend: str | None = None,
    cdp_port: int = DEFAULT_CDP_PORT,
) -> SessionInfo:
    """Extract values from localStorage and/or cookies of a matching Chrome tab.

    Args:
        target_domain: Domain string to match against open Chrome tab URLs.
        local_storage_fields: List of localStorage keys to retrieve.
        cookie_fields: List of cookie names to retrieve (exact match).
        cookie_prefixes: List of cookie name prefixes to retrieve.
            Any cookie whose name starts with one of these prefixes will be included.
        backend: Force a specific backend: ``"applescript"`` or ``"cdp"``.
            When *None* (default), auto-detects based on the current OS —
            AppleScript on macOS, CDP elsewhere.
        cdp_port: Chrome DevTools Protocol port (only used with CDP backend).

    Returns:
        SessionInfo object containing the base URL, localStorage values, and cookies.
    """
    if backend is None:
        backend = "applescript" if platform.system() == "Darwin" else "cdp"

    if backend == "cdp":
        return get_session_info_cdp(
            target_domain=target_domain,
            local_storage_fields=local_storage_fields,
            cookie_fields=cookie_fields,
            cookie_prefixes=cookie_prefixes,
            port=cdp_port,
        )

    # ── AppleScript backend (macOS only) ────────────────────────────────
    return _get_session_info_applescript(
        target_domain=target_domain,
        local_storage_fields=local_storage_fields,
        cookie_fields=cookie_fields,
        cookie_prefixes=cookie_prefixes,
    )


def _get_session_info_applescript(
    target_domain: str,
    local_storage_fields: list[str] | None = None,
    cookie_fields: list[str] | None = None,
    cookie_prefixes: list[str] | None = None,
) -> SessionInfo:
    """Extract session info via AppleScript + browser_cookie3 (macOS only).

    - localStorage  : AppleScript (JS execution in the matching Chrome tab)
    - cookies       : browser_cookie3 — reads Chrome's SQLite DB directly,
                      which allows access to HttpOnly cookies that are invisible
                      to ``document.cookie`` (e.g. ``wordpress_logged_in_*``,
                      ``csrf_token_*``, ``JSESSIONID``).
    """
    needs_cookies = bool(cookie_fields or cookie_prefixes)
    if not local_storage_fields and not needs_cookies:
        raise ValueError("At least one of local_storage_fields, cookie_fields, or cookie_prefixes must be provided.")

    # ── Step 1: find matching tab URL (and optionally localStorage) via AppleScript ──
    if local_storage_fields:
        pairs = ", ".join([f"'{f}': localStorage.getItem('{f}')" for f in local_storage_fields])
        ls_js = f"var ls = {{{pairs}}};"
    else:
        ls_js = "var ls = {};"

    js_snippet = f"{ls_js} JSON.stringify({{ls: ls}});"

    applescript = f"""
    tell application "Google Chrome"
        set foundInfo to "NOT_FOUND"
        repeat with w in windows
            repeat with t in tabs of w
                set currentURL to URL of t
                if currentURL contains "{target_domain}" then
                    set jsResult to execute t javascript "{js_snippet}"
                    if jsResult is not missing value and jsResult is not "" then
                        set foundInfo to jsResult & "||URL||" & currentURL
                        exit repeat
                    end if
                end if
            end repeat
            if foundInfo is not "NOT_FOUND" then exit repeat
        end repeat
        return foundInfo
    end tell
    """

    try:
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)

        if result.returncode != 0:
            stderr_msg = result.stderr.strip()
            if "자바스크립트 허용" in stderr_msg or "Allow JavaScript" in stderr_msg or "Apple Events" in stderr_msg:
                raise TokenRetrievalError(
                    "AppleScript JavaScript execution is disabled in Chrome.\n"
                    "Go to Chrome menu → View → Developer → Enable 'Allow JavaScript from Apple Events'."
                )
            raise TokenRetrievalError(f"AppleScript execution error: {stderr_msg}")

        output = result.stdout.strip()

        if output == "NOT_FOUND" or not output:
            raise TokenRetrievalError(
                f"Could not find a tab with domain '{target_domain}' in Chrome.\n"
                "Please make sure you are logged in on that tab in Chrome."
            )

        json_part, tab_url = output.split("||URL||", 1)
        data = json.loads(json_part)

        parsed = urlparse(tab_url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc
        base_url = f"{scheme}://{netloc}"

        session_info = SessionInfo(base_url=base_url, tab_url=tab_url)

        if local_storage_fields:
            session_info.local_storage = {
                k: (v.strip('"') if isinstance(v, str) else v) for k, v in data.get("ls", {}).items()
            }

        # ── Step 2: collect cookies via browser_cookie3 (includes HttpOnly) ──
        if needs_cookies:
            session_info.cookies = collect_cookies_from_db(
                domain=netloc,
                cookie_fields=cookie_fields,
                cookie_prefixes=cookie_prefixes,
            )

        return session_info

    except TokenRetrievalError:
        raise
    except Exception as e:
        raise TokenRetrievalError(f"Unexpected error while extracting Chrome session info: {e}") from e
