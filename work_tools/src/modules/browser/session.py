import json
import subprocess
from urllib.parse import urlparse

from core.exception import TokenRetrievalError
from modules.browser.schema import SessionInfo


def get_session_info(
    target_domain,
    local_storage_fields: list[str] | None = None,
    cookie_fields: list[str] | None = None,
) -> SessionInfo:
    """
    Extract values from localStorage and/or cookies of a matching Chrome tab.

    Args:
        target_domain: Domain string to match against open Chrome tab URLs.
        local_storage_fields: List of localStorage keys to retrieve.
        cookie_fields: List of cookie names to retrieve.

    Returns:
        SessionInfo object containing the base URL, localStorage values, and cookies.
    """
    if not local_storage_fields and not cookie_fields:
        raise ValueError("At least one of local_storage_fields or cookie_fields must be provided.")

    # Build JavaScript that collects all requested values and returns JSON
    ls_js = ""
    if local_storage_fields:
        pairs = ", ".join([f'\\"{f}\\": localStorage.getItem(\\"{f}\\")' for f in local_storage_fields])
        ls_js = f"var ls = {{{pairs}}};"
    else:
        ls_js = "var ls = {};"

    if cookie_fields:
        # Parse document.cookie and pick requested keys
        cookie_js = (
            "var _cookies = {};"
            "document.cookie.split(';').forEach(function(c) {"
            "  var p = c.trim().split('=');"
            "  var k = p[0]; var v = decodeURIComponent(p.slice(1).join('='));"
            "  _cookies[k] = v;"
            "});"
        )
        pairs = ", ".join([f'\\"{f}\\": (_cookies[\\"{f}\\"] || null)' for f in cookie_fields])
        cookie_js += f"var ck = {{{pairs}}};"
    else:
        cookie_js = "var ck = {};"

    js_snippet = f"{ls_js} {cookie_js} JSON.stringify({{ls: ls, ck: ck}});"

    applescript = f'''
    tell application "Google Chrome"
        set foundInfo to "NOT_FOUND"
        repeat with w in windows
            repeat with t in tabs of w
                set currentURL to URL of t
                if currentURL contains "{target_domain}" then
                    set jsResult to execute t javascript "{js_snippet}"
                    if jsResult is not missing value and jsResult is not "" then
                        set foundInfo to jsResult & "|" & currentURL
                        exit repeat
                    end if
                end if
            end repeat
            if foundInfo is not "NOT_FOUND" then exit repeat
        end repeat
        return foundInfo
    end tell
    '''

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

        json_part, tab_url = output.split("|", 1)
        data = json.loads(json_part)

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
        if cookie_fields:
            session_info.cookies = data.get("ck", {})

        return session_info

    except TokenRetrievalError:
        raise
    except Exception as e:
        raise TokenRetrievalError(f"Unexpected error while extracting Chrome session info: {e}") from e
