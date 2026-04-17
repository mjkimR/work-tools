"""
Read cookies directly from Chrome's SQLite DB via browser_cookie3.

Unlike ``document.cookie`` (which is limited to non-HttpOnly cookies), this
module reads the raw cookie store and can access **HttpOnly** cookies such as
``wordpress_logged_in_*``, ``csrf_token_*``, and ``JSESSIONID``.

Works on **macOS, Windows, and Linux** — browser_cookie3 handles platform
differences internally (Keychain / DPAPI / libsecret).
"""

import browser_cookie3
from work_tools.core.exception import TokenRetrievalError


def collect_cookies_from_db(
    domain: str,
    cookie_fields: list[str] | None,
    cookie_prefixes: list[str] | None,
) -> dict[str, str]:
    """Read cookies directly from Chrome's SQLite DB via browser_cookie3.

    Unlike ``document.cookie``, this method can access HttpOnly cookies such as
    ``wordpress_logged_in_*``, ``csrf_token_*``, and ``JSESSIONID``.

    Some cookies (e.g. ``csrf_token_*``, ``JSESSIONID``) are registered on the
    parent domain (e.g. ``.company.co.kr``) rather than the exact hostname, so we
    query both the exact hostname and all its parent domains to make sure nothing
    is missed.

    Works on macOS, Windows, and Linux.
    - macOS  : extracts the encryption key from Keychain
    - Windows: extracts the encryption key via DPAPI
    - Linux  : uses libsecret or kwallet

    Args:
        domain: Hostname to filter (e.g. ``developer.company.co.kr``).
        cookie_fields: Exact cookie names to include.
        cookie_prefixes: Cookie name prefixes to include.

    Returns:
        Dict of ``{name: value}`` for matching cookies.
    """
    # Build a set of domain variants to match against:
    #   "developer.company.co.kr" → {"developer.company.co.kr", ".company.co.kr", ...}
    parts = domain.lstrip(".").split(".")
    domains_to_match: set[str] = {domain}
    # Add parent domains with leading dot (e.g. .company.co.kr, .co.kr)
    for i in range(1, len(parts) - 1):
        domains_to_match.add("." + ".".join(parts[i:]))

    try:
        all_cookies: list = list(browser_cookie3.chrome())
    except Exception as e:
        raise TokenRetrievalError(
            f"browser_cookie3 failed to read Chrome cookies: {e}\n"
            "Make sure Chrome is installed and you have granted Full Disk Access if required."
        ) from e

    seen: set[str] = set()
    result: dict[str, str] = {}
    for cookie in all_cookies:
        # Filter by domain in Python (replaces domain_name= per-call approach)
        cookie_domain = cookie.domain or ""
        if cookie_domain not in domains_to_match:
            continue

        name = cookie.name
        if name in seen:
            continue

        value = cookie.value or ""
        matched = False

        if cookie_fields and name in cookie_fields:
            matched = True

        if not matched and cookie_prefixes:
            for prefix in cookie_prefixes:
                if name.startswith(prefix):
                    matched = True
                    break

        if matched:
            result[name] = value
            seen.add(name)

    return result
