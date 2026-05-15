from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import httpx
from work_tools.core.exception import TokenExpiredError, TokenRetrievalError
from work_tools.core.log import logger
from work_tools.modules.browser.schema import SessionInfo
from work_tools.modules.browser.session import get_session_info
from work_tools.modules.browser.session_cache import SessionCache


class AuthMode(Enum):
    """Authentication mode for browser-based API clients."""

    BEARER = "bearer"
    COOKIE = "cookie"


class BrowserTokenBaseClient(ABC):
    """Base class for HTTP API clients that authenticate via browser session discovery.

    Discovers auth credentials (Bearer token or cookies) from a running Chrome browser,
    creates a shared ``httpx.Client`` (sync) once per instance, and provides helper
    methods for common HTTP verbs with automatic token-expiration detection.

    Subclasses must implement:
        - ``domain``: the domain string used to match the Chrome tab.
        - ``auth_mode``: whether the API uses Bearer tokens or cookies.
        - ``local_storage_fields`` / ``cookie_fields``: which browser values to fetch.

    Attributes:
        session_info: The discovered ``SessionInfo`` from the browser.
        base_url: Base URL for API requests (derived from the browser tab).
        http: The ``httpx.Client`` instance shared for the lifetime of this client.
    """

    # ── Subclass configuration ──────────────────────────────────────────

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain substring to match against open Chrome tab URLs."""
        ...

    @property
    @abstractmethod
    def auth_mode(self) -> AuthMode:
        """Authentication strategy (BEARER or COOKIE)."""
        ...

    @property
    def local_storage_fields(self) -> list[str] | None:
        """localStorage keys to retrieve from the browser (used for BEARER mode)."""
        return None

    @property
    def cookie_fields(self) -> list[str] | None:
        """Cookie names to retrieve from the browser (used for COOKIE mode)."""
        return None

    @property
    def cookie_prefixes(self) -> list[str] | None:
        """Cookie name prefixes to retrieve from the browser (used for COOKIE mode).

        Any cookie whose name starts with one of these prefixes will be included.
        Useful for cookies like ``wordpress_logged_in_{hash}`` where the suffix varies.
        """
        return None

    @property
    def base_url_suffix(self) -> str:
        """Path suffix appended to the discovered base URL (e.g. ``/api/v1``).

        Override in subclass to target a specific API path prefix.
        """
        return ""

    @property
    def unauthorized_status_codes(self) -> set[int]:
        """HTTP status codes that indicate token/session expiration.

        Override in subclass if the target API uses different codes.
        """
        return {401, 403}

    @property
    def default_headers(self) -> dict[str, str]:
        """Extra headers merged into every request beyond auth headers.

        Override in subclasses to add User-Agent, Referer, Accept, etc.
        """
        return {}

    # ── Lifecycle ───────────────────────────────────────────────────────

    def __init__(self, base_url_override: str | None = None):
        """Discover session credentials from Chrome and build an httpx.Client.

        On the first call for a given domain the credentials are fetched from the
        running Chrome browser and persisted to a local cache file.  Subsequent
        calls within the configured TTL reuse the cached credentials without
        touching the browser.

        Args:
            base_url_override: If provided, use this as the API base URL
                               instead of the one derived from the browser tab.
        """
        self._session_cache: SessionCache = SessionCache(self.domain)
        self.session_info: SessionInfo = self._get_session_info_with_cache()

        discovered = base_url_override or self.session_info.base_url
        self.base_url: str = f"{discovered}{self.base_url_suffix}"

        headers, cookies = self._build_auth()
        headers = {**self.default_headers, **headers}
        self.http: httpx.Client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            cookies=cookies,
            timeout=30.0,
        )

    # ── Session / cache helpers ─────────────────────────────────────────

    def _get_session_info_with_cache(self) -> SessionInfo:
        """Return a ``SessionInfo``, preferring a valid cached entry.

        Flow:
          1. Try to load from cache → return if valid.
          2. Fetch fresh from the browser → save to cache → return.
          3. If both fail, re-raise the original ``TokenRetrievalError``.
        """
        cached = self._session_cache.load()
        if cached is not None:
            return cached

        logger.debug(f"[SessionCache] Cache miss for '{self.domain}'. Fetching from browser…")
        session_info = get_session_info(
            target_domain=self.domain,
            local_storage_fields=self.local_storage_fields,
            cookie_fields=self.cookie_fields,
            cookie_prefixes=self.cookie_prefixes,
        )
        self._session_cache.save(session_info)
        return session_info

    def _rebuild_http_client(self) -> None:
        """Close the current httpx.Client and build a new one from ``self.session_info``."""
        try:
            self.http.close()
        except Exception as exc:
            logger.debug(f"Failed to close HTTP client during rebuild: {exc}")

        headers, cookies = self._build_auth()
        headers = {**self.default_headers, **headers}
        self.http = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            cookies=cookies,
            timeout=30.0,
        )

    # ── Auth helpers ────────────────────────────────────────────────────

    def _build_auth(self) -> tuple[dict[str, str], dict[str, str]]:
        """Build headers and cookies dicts from the discovered session info."""
        headers: dict[str, str] = {}
        cookies: dict[str, str] = {}

        if self.auth_mode == AuthMode.BEARER:
            token = self._extract_bearer_token()
            headers["Authorization"] = f"Bearer {token}"
            headers["Content-Type"] = "application/json"
        elif self.auth_mode == AuthMode.COOKIE:
            cookies = self._extract_cookies()
        else:
            raise ValueError(f"Unknown auth mode: {self.auth_mode}")

        return headers, cookies

    def _extract_bearer_token(self) -> str:
        """Return the bearer token from local_storage, raising on failure."""
        fields = self.local_storage_fields or []
        for field in fields:
            value = self.session_info.local_storage.get(field)
            if value:
                return value
        raise TokenRetrievalError(
            f"Could not find a valid bearer token in localStorage fields {fields} for domain '{self.domain}'."
        )

    def _extract_cookies(self) -> dict[str, str]:
        """Return a cookie dict from the discovered session info."""
        raw = self.session_info.cookies or {}
        result = {k: v for k, v in raw.items() if v is not None}
        if not result:
            raise TokenRetrievalError(
                f"Could not find valid cookies for domain '{self.domain}'. "
                "Please make sure you are logged in on that tab in Chrome."
            )
        return result

    # ── Request helpers ─────────────────────────────────────────────────

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send an HTTP request via the shared httpx.Client.

        Raises ``TokenExpiredError`` with a user-friendly message when the
        server responds with an unauthorized status code.

        Args:
            method: HTTP method (GET, POST, PATCH, PUT, DELETE …).
            path: URL path relative to ``base_url``.
            params: Query parameters.
            json: JSON body (mutually exclusive with *data*).
            data: Form-encoded body.
            headers: Extra headers merged with the client defaults.
            **kwargs: Passed through to ``httpx.Client.request``.

        Returns:
            The ``httpx.Response`` object.
        """
        response = self.http.request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            **kwargs,
        )

        if response.status_code in self.unauthorized_status_codes:
            self._handle_unauthorized(response)

        return response

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Shortcut for ``self.request("GET", ...)``. Returns ``httpx.Response``."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Shortcut for ``self.request("POST", ...)``. Returns ``httpx.Response``."""
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        """Shortcut for ``self.request("PATCH", ...)``. Returns ``httpx.Response``."""
        return self.request("PATCH", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Shortcut for ``self.request("PUT", ...)``. Returns ``httpx.Response``."""
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Shortcut for ``self.request("DELETE", ...)``. Returns ``httpx.Response``."""
        return self.request("DELETE", path, **kwargs)

    # ── Token expiry handling ───────────────────────────────────────────

    def _handle_unauthorized(self, response: httpx.Response) -> None:
        """Invalidate the session cache, refresh credentials from the browser,
        and raise ``TokenExpiredError`` if the refresh also fails.

        Override in subclasses to customise recovery behaviour.
        """
        auth_label = "token" if self.auth_mode == AuthMode.BEARER else "cookie/session"
        logger.warning(
            f"[{response.status_code}] Auth error for '{self.domain}'. "
            "Invalidating cache and refreshing session from browser…"
        )

        self._session_cache.invalidate()
        try:
            self.session_info = get_session_info(
                target_domain=self.domain,
                local_storage_fields=self.local_storage_fields,
                cookie_fields=self.cookie_fields,
                cookie_prefixes=self.cookie_prefixes,
            )
            self._session_cache.save(self.session_info)
            self._rebuild_http_client()
            logger.debug(f"[SessionCache] Session refreshed successfully for '{self.domain}'.")
        except Exception as refresh_exc:
            msg = (
                f"[{response.status_code}] API request failed due to an authentication error.\n"
                f"  -> The {auth_label} for '{self.domain}' tab in your browser may have expired.\n"
                f"  -> Please log in to the service again in your browser and retry.\n"
                f"  -> Response body: {response.text[:300]}\n"
                f"  -> Refresh error: {refresh_exc}"
            )
            logger.error(msg)
            raise TokenExpiredError(msg) from refresh_exc

    # ── Cleanup ─────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying httpx.Client."""
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        try:
            self.http.close()
        except Exception as exc:
            logger.debug(f"Failed to close HTTP client during deletion: {exc}")

