"""Tests for DocsLoader."""

import pytest
import yaml
from modules.docs.config import DocsSettings
from modules.docs.loader import DocsLoader, _mask_value


def dummy_generator() -> str:
    """A dummy generator for testing dynamic generator loading."""
    return "Dummy Data Output"


@pytest.fixture
def temp_docs_env(tmp_path):
    """Create a temporary docs environment with a fake manifest and references."""
    ref_dir = tmp_path / "references"
    ref_dir.mkdir()
    (ref_dir / "test_ref.md").write_text("Hello from Reference", encoding="utf-8")

    manifest_path = tmp_path / "docs_manifest.yaml"
    manifest_data = {
        "subjects": {
            "test_sub": {
                "description": "A test subject.\nSecond line.",
                "references": ["test_ref.md", "missing_ref.md"],
                "env_vars": ["TEST_VAR", "TEST_SECRET_KEY", "MISSING_VAR"],
                "generators": ["tests.unit.docs.test_loader:dummy_generator", "bad.module:bad_func"],
            }
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest_data, f)

    return DocsSettings(
        DOCS_REFERENCES_DIR=str(ref_dir),  # type: ignore[call-arg]
        DOCS_MANIFEST_PATH=str(manifest_path),  # type: ignore[call-arg]
    )


class TestDocsLoader:
    def test_list_subjects(self, temp_docs_env):
        loader = DocsLoader(settings=temp_docs_env)
        assert loader.list_subjects() == ["test_sub"]

    def test_list_subjects_with_descriptions(self, temp_docs_env):
        loader = DocsLoader(settings=temp_docs_env)
        descs = loader.list_subjects_with_descriptions()
        assert descs["test_sub"] == "A test subject."

    def test_load_composes_correctly(self, temp_docs_env, monkeypatch):
        loader = DocsLoader(settings=temp_docs_env)
        monkeypatch.setenv("TEST_VAR", "visible_value")
        # Masking should occur for keys with SECRET
        monkeypatch.setenv("TEST_SECRET_KEY", "supersecret")
        monkeypatch.delenv("MISSING_VAR", raising=False)

        result = loader.load("test_sub")

        # Header checking
        assert "# Context: test_sub" in result
        assert "A test subject.\nSecond line." in result

        # References checking
        assert "## 📄 test_ref.md" in result
        assert "Hello from Reference" in result
        assert "## 📄 missing_ref.md" in result
        assert "⚠️ File not found" in result

        # Environment checking
        assert "`TEST_VAR`: `visible_value`" in result
        assert "`TEST_SECRET_KEY`: `su***et`" in result
        assert "`MISSING_VAR`: `<NOT SET>`" in result

        # Generator checking
        assert "## ⚙️ Dynamic: tests.unit.docs.test_loader:dummy_generator" in result
        assert "Dummy Data Output" in result
        assert "## ⚙️ Dynamic: bad.module:bad_func" in result
        assert "⚠️ Generator error" in result

    def test_load_missing_subject_raises(self, temp_docs_env):
        loader = DocsLoader(settings=temp_docs_env)
        with pytest.raises(KeyError, match="not found"):
            loader.load("non_existent")


class TestMaskValue:
    def test_no_masking(self):
        assert _mask_value("NORMAL_VAR", "raw_value") == "raw_value"

    def test_short_secret(self):
        assert _mask_value("API_KEY", "abc") == "***"

    def test_long_secret(self):
        assert _mask_value("MY_PASSWORD", "1234567890") == "12***90"
