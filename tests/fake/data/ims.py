"""Hardcoded response data for FakeImsClient.

Mirrors the HTML structures returned by the real IMS (KBoard/WordPress)
so that handler/client tests can run without any network access.
"""

import pathlib

_DATA_DIR = pathlib.Path(__file__).parent

SAMPLE_DOCUMENT_HTML = (_DATA_DIR / "sample_document.html").read_text(encoding="utf-8")
LOGIN_REQUIRED_HTML = (_DATA_DIR / "login_required.html").read_text(encoding="utf-8")
