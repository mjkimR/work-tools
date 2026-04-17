"""Tests for DocsCLIHandlers — Integration flow using fake docs_manifest.yaml."""

import pytest
import yaml
from work_tools.modules.docs.config import DocsSettings
from work_tools.modules.docs.handler import DocsCLIHandlers
from work_tools.modules.docs.loader import DocsLoader


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
    monkeypatch.setattr("work_tools.modules.docs.loader.get_docs_settings", lambda: settings)
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


class TestDocsManifestIntegrity:
    """Validates that docs_manifest.yaml is in sync with the actual references directory.

    These tests guard against silent context injection failures caused by:
    - A reference file declared in the manifest that no longer exists on disk.
    - A reference file added to the references/ directory without being declared in any subject.
    """

    @pytest.fixture
    def real_loader(self):
        """DocsLoader backed by the real docs_manifest.yaml and references/ directory."""
        return DocsLoader()

    def test_all_declared_references_exist_on_disk(self, real_loader):
        """Every reference path declared in docs_manifest.yaml must exist on disk.

        Catches: file renamed/deleted after being registered in the manifest.
        """
        ref_root = real_loader.settings.resolve_references_dir()
        missing = []
        for subject, entry in real_loader.manifest.subjects.items():
            for ref_path in entry.references:
                abs_path = ref_root / ref_path
                if not abs_path.exists():
                    missing.append(f"[{subject}] {ref_path}")

        assert not missing, (
            "The following reference files are declared in docs_manifest.yaml but not found on disk:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    def test_all_reference_files_declared_in_manifest(self, real_loader):
        """Every .md file in references/ must be declared in at least one manifest subject.

        Catches: a new guideline file added to references/ without being registered in the manifest,
        which would cause it to never be injected as context.
        """
        ref_root = real_loader.settings.resolve_references_dir()
        declared = {ref for entry in real_loader.manifest.subjects.values() for ref in entry.references}
        all_files = {f.name for f in ref_root.glob("*.md")}
        undeclared = all_files - declared

        assert not undeclared, (
            "The following files exist in references/ but are not declared in any subject in docs_manifest.yaml:\n"
            + "\n".join(f"  - {f}" for f in sorted(undeclared))
        )
