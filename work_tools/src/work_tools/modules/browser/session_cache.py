"""Browser session cache for storing and reusing auth credentials.

Caches ``SessionInfo`` (cookies / localStorage tokens) to disk as JSON files
under ``{git_repo_root}/.cache/browser_session/{domain}.json``.

TTL defaults to **86 400 seconds (1 day)** and can be overridden via the
``BROWSER_SESSION_CACHE_TTL_SECONDS`` environment variable.
"""

from __future__ import annotations

import base64
import json
import os
import binascii
import time
from pathlib import Path

from work_tools.core.log import logger
from work_tools.modules.browser.schema import SessionInfo

_DEFAULT_TTL_SECONDS = 86_400  # 24 hours
_CACHE_TTL_ENV_VAR = "BROWSER_SESSION_CACHE_TTL_SECONDS"
_CACHE_SUBDIR = ".cache/browser_session"


def _get_cache_dir() -> Path | None:
    """Return the cache directory path, or None if the git root cannot be found."""
    try:
        from work_tools.core.util.project_path import get_git_repo_root

        root = get_git_repo_root()
        return Path(root) / _CACHE_SUBDIR
    except Exception as exc:
        logger.warning(f"[SessionCache] Could not determine git repo root — caching disabled: {exc}")
        return None


def _get_ttl() -> int:
    """Return the effective TTL in seconds from env var or default."""
    raw = os.environ.get(_CACHE_TTL_ENV_VAR)
    if raw is not None:
        try:
            return int(raw)
        except ValueError:
            logger.warning(
                f"[SessionCache] Invalid value for {_CACHE_TTL_ENV_VAR}={raw!r}; "
                f"falling back to default {_DEFAULT_TTL_SECONDS}s."
            )
    return _DEFAULT_TTL_SECONDS


def _encode_values(d: dict) -> dict:
    """Base64-encode every string value in a (possibly nested) dict."""
    result = {}
    for k, v in d.items():
        if isinstance(v, str):
            result[k] = base64.b64encode(v.encode()).decode()
        elif isinstance(v, dict):
            result[k] = _encode_values(v)
        else:
            result[k] = v
    return result


def _decode_values(d: dict) -> dict:
    """Base64-decode every string value in a (possibly nested) dict."""
    result = {}
    for k, v in d.items():
        if isinstance(v, str):
            try:
                result[k] = base64.b64decode(v.encode()).decode()
            except (binascii.Error, UnicodeDecodeError, ValueError):
                # Maintain original when decoding fails (backward compatibility for previous cache)
                result[k] = v
        elif isinstance(v, dict):
            result[k] = _decode_values(v)
        else:
            result[k] = v
    return result


class SessionCache:
    """Disk-based cache for a single domain's ``SessionInfo``.

    Cache files are stored at::

        {git_repo_root}/.cache/browser_session/{safe_domain}.json

    Each file contains the serialised ``SessionInfo`` plus a ``"cached_at"``
    UNIX timestamp used to enforce the TTL.

    Args:
        domain: The domain string used as the cache key (file name).
    """

    def __init__(self, domain: str) -> None:
        self._domain = domain
        self._safe_name = domain.replace("/", "_").replace(":", "_")
        self._cache_dir = _get_cache_dir()
        self._ttl = _get_ttl()

    @property
    def _cache_file(self) -> Path | None:
        if self._cache_dir is None:
            return None
        return self._cache_dir / f"{self._safe_name}.json"

    # ── Public API ──────────────────────────────────────────────────────

    def load(self) -> SessionInfo | None:
        """Load a valid (non-expired) ``SessionInfo`` from the cache.

        Returns:
            ``SessionInfo`` if the cache file exists and is within TTL,
            otherwise ``None``.
        """
        path = self._cache_file
        if path is None or not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            cached_at: float = raw.pop("cached_at", 0)
            age = time.time() - cached_at
            if age > self._ttl:
                logger.debug(
                    f"[SessionCache] Cache for '{self._domain}' expired ({age:.0f}s > TTL {self._ttl}s). Discarding."
                )
                return None
            logger.debug(f"[SessionCache] Cache hit for '{self._domain}' (age {age:.0f}s).")
            return SessionInfo(**_decode_values(raw))
        except Exception as exc:
            logger.warning(f"[SessionCache] Failed to read cache for '{self._domain}': {exc}")
            return None

    def save(self, session_info: SessionInfo) -> None:
        """Persist *session_info* to the cache file.

        Creates the cache directory if it does not exist.
        Silently ignores write errors so that caching failures never break
        the main flow.
        """
        path = self._cache_file
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = _encode_values(session_info.model_dump())
            data["cached_at"] = time.time()
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.debug(f"[SessionCache] Saved cache for '{self._domain}' → {path}")
        except Exception as exc:
            logger.warning(f"[SessionCache] Failed to write cache for '{self._domain}': {exc}")

    def invalidate(self) -> None:
        """Delete the cache file for this domain, if it exists."""
        path = self._cache_file
        if path is None or not path.exists():
            return
        try:
            path.unlink()
            logger.debug(f"[SessionCache] Invalidated cache for '{self._domain}'.")
        except Exception as exc:
            logger.warning(f"[SessionCache] Failed to invalidate cache for '{self._domain}': {exc}")
