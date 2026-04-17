"""Unit tests for BrowserTokenBaseClient caching behaviour.

All Chrome / browser I/O is mocked out — no actual browser interaction occurs.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from work_tools.core.exception import TokenExpiredError, TokenRetrievalError
from work_tools.modules.browser.client import AuthMode, BrowserTokenBaseClient
from work_tools.modules.browser.schema import SessionInfo
from work_tools.modules.browser.session_cache import SessionCache

# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------


class FakeClient(BrowserTokenBaseClient):
    domain = "fake.example.com"
    auth_mode = AuthMode.BEARER
    local_storage_fields = ["auth_token"]


def _make_session(token: str = "tok-1") -> SessionInfo:
    return SessionInfo(
        base_url="https://fake.example.com",
        tab_url="https://fake.example.com/app",
        local_storage={"auth_token": token},
    )


def _make_cache(tmp_path: Path, domain: str = "fake.example.com") -> SessionCache:
    cache = SessionCache(domain)
    cache._cache_dir = tmp_path / ".cache" / "browser_session"
    cache._ttl = 3600
    return cache


def _make_client(tmp_path: Path, session: SessionInfo | None = None) -> FakeClient:
    """Build a FakeClient with all external I/O mocked.

    - ``get_session_info`` is mocked to return *session* (default: _make_session()).
    - The cache dir is redirected to *tmp_path*.

    The patch stays active during the entire client construction so that
    ``_get_session_info_with_cache`` (which calls ``get_session_info`` on cache
    miss) can be properly intercepted.
    """
    if session is None:
        session = _make_session()

    patcher = patch("work_tools.modules.browser.client.get_session_info", return_value=session)
    patcher.start()
    try:
        client = FakeClient.__new__(FakeClient)
        client._session_cache = _make_cache(tmp_path)
        client.session_info = client._get_session_info_with_cache()
        client.base_url = f"{session.base_url}{client.base_url_suffix}"
        headers, cookies = client._build_auth()
        headers = {**client.default_headers, **headers}
        client.http = httpx.Client(
            base_url=client.base_url,
            headers=headers,
            cookies=cookies,
            timeout=30.0,
        )
    finally:
        patcher.stop()
    return client


# ---------------------------------------------------------------------------
# Cache miss → browser fetch → cache saved
# ---------------------------------------------------------------------------


class TestCacheMissFlow:
    def test_browser_fetched_on_cache_miss(self, tmp_path):
        """Browser get_session_info is called exactly once on a cold cache."""
        session = _make_session()
        with patch("work_tools.modules.browser.client.get_session_info", return_value=session) as mock_get:
            client = FakeClient.__new__(FakeClient)
            client._session_cache = _make_cache(tmp_path)
            client.session_info = client._get_session_info_with_cache()

        mock_get.assert_called_once()
        assert client.session_info.local_storage["auth_token"] == "tok-1"

    def test_cache_file_written_after_browser_fetch(self, tmp_path):
        client = _make_client(tmp_path)
        assert client._session_cache._cache_file.exists()

    def test_retrieval_error_propagates(self, tmp_path):
        with patch(
            "work_tools.modules.browser.client.get_session_info",
            side_effect=TokenRetrievalError("no tab found"),
        ):
            client = FakeClient.__new__(FakeClient)
            client._session_cache = _make_cache(tmp_path)
            with pytest.raises(TokenRetrievalError, match="no tab found"):
                client._get_session_info_with_cache()


# ---------------------------------------------------------------------------
# Cache hit → browser NOT called
# ---------------------------------------------------------------------------


class TestCacheHitFlow:
    def test_browser_not_called_when_cache_valid(self, tmp_path):
        # Pre-populate the cache
        initial_session = _make_session("tok-cached")
        cache = _make_cache(tmp_path)
        cache.save(initial_session)

        with patch("work_tools.modules.browser.client.get_session_info") as mock_get:
            client = FakeClient.__new__(FakeClient)
            client._session_cache = cache
            client.session_info = client._get_session_info_with_cache()

        mock_get.assert_not_called()
        assert client.session_info.local_storage["auth_token"] == "tok-cached"


# ---------------------------------------------------------------------------
# _handle_unauthorized → cache invalidate → browser re-fetch → client rebuilt
# ---------------------------------------------------------------------------


class TestHandleUnauthorized:
    def _make_response(self, status_code: int = 401) -> httpx.Response:
        return httpx.Response(status_code, text="Unauthorized")

    def test_cache_invalidated_on_unauthorized(self, tmp_path):
        client = _make_client(tmp_path)
        client._session_cache.save(client.session_info)  # ensure file exists

        new_session = _make_session("tok-refreshed")
        with patch("work_tools.modules.browser.client.get_session_info", return_value=new_session):
            client._handle_unauthorized(self._make_response(401))

        # Cache file should contain fresh token
        loaded = client._session_cache.load()
        assert loaded is not None
        assert loaded.local_storage["auth_token"] == "tok-refreshed"

    def test_session_info_updated_after_refresh(self, tmp_path):
        client = _make_client(tmp_path)
        new_session = _make_session("tok-new")

        with patch("work_tools.modules.browser.client.get_session_info", return_value=new_session):
            client._handle_unauthorized(self._make_response(401))

        assert client.session_info.local_storage["auth_token"] == "tok-new"

    def test_raises_token_expired_error_when_refresh_fails(self, tmp_path):
        client = _make_client(tmp_path)

        with patch(
            "work_tools.modules.browser.client.get_session_info",
            side_effect=TokenRetrievalError("browser unavailable"),
        ):
            with pytest.raises(TokenExpiredError):
                client._handle_unauthorized(self._make_response(401))

    def test_cache_file_absent_after_failed_refresh(self, tmp_path):
        client = _make_client(tmp_path)
        client._session_cache.save(client.session_info)

        with patch(
            "work_tools.modules.browser.client.get_session_info",
            side_effect=TokenRetrievalError("browser unavailable"),
        ):
            with pytest.raises(TokenExpiredError):
                client._handle_unauthorized(self._make_response(401))

        # Cache must have been invalidated (file removed)
        assert not client._session_cache._cache_file.exists()
