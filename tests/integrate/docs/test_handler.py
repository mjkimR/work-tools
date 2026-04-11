"""Tests for DocsCLIHandlers — Integration flow using fake docs_manifest.yaml."""

import pytest
import yaml
from modules.docs.config import DocsSettings
from modules.docs.handler import DocsCLIHandlers


@pytest.fixture
def fake_docs_env(tmp_path, monkeypatch):
    """Fixture that intercepts DocsLoader settings to use a fake manifest."""
    manifest_path = tmp_path / "docs_manifest.yaml"
    manifest_data = {"subjects": {"test_subject": {"description": "Integration Test Subject"}}}
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest_data, f)

    settings = DocsSettings(
        DOCS_REFERENCES_DIR=str(tmp_path),  # type: ignore[call-arg]
        DOCS_MANIFEST_PATH=str(manifest_path),  # type: ignore[call-arg]
    )  # Patch get_docs_settings so that DocsLoader() inside Handler picks it up
    monkeypatch.setattr("modules.docs.loader.get_docs_settings", lambda: settings)
    return settings


class TestDocsCLIHandlers:
    def test_read_docs_success(self, fake_docs_env, capsys):
        handler = DocsCLIHandlers()
        handler.read_docs("test_subject")

        out = capsys.readouterr().out
        assert "# Context: test_subject" in out
        assert "Integration Test Subject" in out

    def test_read_docs_missing_subject_raises(self, fake_docs_env):
        handler = DocsCLIHandlers()
        with pytest.raises(KeyError, match="not found"):
            handler.read_docs("unknown_subject")
