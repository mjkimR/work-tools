"""Unit tests for modules.browser.session_cache.SessionCache."""

from __future__ import annotations

import json
import time
from pathlib import Path

from work_tools.modules.browser import session_cache as session_cache_module
from work_tools.modules.browser.schema import SessionInfo
from work_tools.modules.browser.session_cache import SessionCache

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(domain: str = "example.com") -> SessionInfo:
    return SessionInfo(
        base_url=f"https://{domain}",
        tab_url=f"https://{domain}/page",
        local_storage={"token": "abc123"},
        cookies={"session": "xyz"},
    )


def _make_cache(tmp_path: Path, domain: str = "example.com") -> SessionCache:
    """Create a SessionCache whose cache dir is inside pytest's tmp_path."""
    cache = SessionCache(domain)
    cache._cache_dir = tmp_path / ".cache" / "browser_session"
    cache._ttl = 3600  # 1 hour default for tests
    return cache


# ---------------------------------------------------------------------------
# save / load — happy path
# ---------------------------------------------------------------------------


class TestSessionCacheSaveLoad:
    def test_save_creates_file(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.save(_make_session())

        assert cache._cache_file.exists()

    def test_load_returns_session_info(self, tmp_path):
        cache = _make_cache(tmp_path)
        original = _make_session()
        cache.save(original)

        loaded = cache.load()

        assert loaded is not None
        assert loaded.base_url == original.base_url
        assert loaded.tab_url == original.tab_url
        assert loaded.local_storage == original.local_storage
        assert loaded.cookies == original.cookies

    def test_saved_file_contains_cached_at(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.save(_make_session())

        raw = json.loads(cache._cache_file.read_text())
        assert "cached_at" in raw
        assert raw["cached_at"] > 0

    def test_load_when_no_file_returns_none(self, tmp_path):
        cache = _make_cache(tmp_path)
        assert cache.load() is None


# ---------------------------------------------------------------------------
# TTL expiry
# ---------------------------------------------------------------------------


class TestSessionCacheTTL:
    def test_load_returns_none_when_expired(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache._ttl = 10  # 10 seconds TTL

        # Write a cache entry timestamped 1 hour ago (well past TTL)
        data = _make_session().model_dump()
        data["cached_at"] = time.time() - 3600
        cache._cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache._cache_file.write_text(json.dumps(data), encoding="utf-8")

        assert cache.load() is None

    def test_load_returns_session_when_within_ttl(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache._ttl = 3600

        data = _make_session().model_dump()
        data["cached_at"] = time.time() - 60  # 1 minute ago → still valid
        cache._cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache._cache_file.write_text(json.dumps(data), encoding="utf-8")

        loaded = cache.load()
        assert loaded is not None

    def test_ttl_env_override(self, monkeypatch):
        monkeypatch.setenv("BROWSER_SESSION_CACHE_TTL_SECONDS", "7200")
        from work_tools.modules.browser.session_cache import _get_ttl

        assert _get_ttl() == 7200

    def test_ttl_invalid_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("BROWSER_SESSION_CACHE_TTL_SECONDS", "not_a_number")
        from work_tools.modules.browser.session_cache import _DEFAULT_TTL_SECONDS, _get_ttl

        assert _get_ttl() == _DEFAULT_TTL_SECONDS

    def test_ttl_default_is_one_day(self):
        from work_tools.modules.browser.session_cache import _DEFAULT_TTL_SECONDS

        assert _DEFAULT_TTL_SECONDS == 86_400


# ---------------------------------------------------------------------------
# cache directory selection
# ---------------------------------------------------------------------------


class TestSessionCacheDir:
    def test_cache_dir_env_override(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "browser-session-cache"
        monkeypatch.setenv("WT_BROWSER_SESSION_CACHE_DIR", str(cache_dir))

        assert session_cache_module._get_cache_dir() == cache_dir

    def test_cache_dir_falls_back_to_workspace_when_user_cache_unwritable(self, tmp_path, monkeypatch):
        user_cache = tmp_path / "blocked-user-cache"
        calls = []

        def fake_ensure_writable_dir(path):
            calls.append(path)
            return path != user_cache

        monkeypatch.delenv("WT_BROWSER_SESSION_CACHE_DIR", raising=False)
        monkeypatch.setattr(session_cache_module, "_user_cache_dir", lambda: user_cache)
        monkeypatch.setattr(session_cache_module, "_ensure_writable_dir", fake_ensure_writable_dir)
        monkeypatch.chdir(tmp_path)

        assert session_cache_module._get_cache_dir() == tmp_path / ".work-tools-cache" / "browser_session"
        assert calls == [user_cache, tmp_path / ".work-tools-cache" / "browser_session"]


# ---------------------------------------------------------------------------
# invalidate
# ---------------------------------------------------------------------------


class TestSessionCacheInvalidate:
    def test_invalidate_removes_file(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.save(_make_session())
        assert cache._cache_file.exists()

        cache.invalidate()

        assert not cache._cache_file.exists()

    def test_invalidate_when_no_file_is_noop(self, tmp_path):
        cache = _make_cache(tmp_path)
        # Should not raise
        cache.invalidate()

    def test_load_after_invalidate_returns_none(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.save(_make_session())
        cache.invalidate()

        assert cache.load() is None


# ---------------------------------------------------------------------------
# Disabled cache (no git root)
# ---------------------------------------------------------------------------


class TestSessionCacheDisabled:
    def test_save_is_noop_when_cache_dir_is_none(self):
        cache = SessionCache("example.com")
        cache._cache_dir = None  # simulate git root not found

        # Should not raise
        cache.save(_make_session())

    def test_load_returns_none_when_cache_dir_is_none(self):
        cache = SessionCache("example.com")
        cache._cache_dir = None

        assert cache.load() is None

    def test_invalidate_is_noop_when_cache_dir_is_none(self):
        cache = SessionCache("example.com")
        cache._cache_dir = None

        # Should not raise
        cache.invalidate()


# ---------------------------------------------------------------------------
# safe_name (domain → filename)
# ---------------------------------------------------------------------------


class TestSessionCacheSafeName:
    def test_forward_slash_replaced(self):
        cache = SessionCache("example.com/path")
        assert "/" not in cache._safe_name

    def test_colon_replaced(self):
        cache = SessionCache("http:example.com")
        assert ":" not in cache._safe_name

    def test_plain_domain_unchanged(self):
        cache = SessionCache("example.com")
        assert cache._safe_name == "example.com"


# ---------------------------------------------------------------------------
# Corrupt cache file
# ---------------------------------------------------------------------------


class TestSessionCacheCorruptFile:
    def test_load_returns_none_on_corrupt_json(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache._cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache._cache_file.write_text("not valid json {{{", encoding="utf-8")

        assert cache.load() is None
