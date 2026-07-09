"""Tests for DocsCLIHandlers — Integration flow using fake docs_manifest.yaml."""

import importlib
import re

import pytest
import yaml
from work_tools.modules.docs.config import DocsSettings
from work_tools.modules.docs.handler import DocsCLIHandlers
from work_tools.modules.docs.loader import DocsLoader

# A reference file declares the flags it forbids with a marker placed next to the rule:
#     <!-- forbidden-flags: --status -->
_FORBIDDEN_MARKER = re.compile(r"<!--\s*forbidden-flags:\s*(?P<flags>[^>]+?)\s*-->")

# Subjects SKILL.md tells the agent to load, e.g. ``wt docs read-docs task-writer``.
# Stops at a backtick or paren so surrounding Markdown is not captured.
_READ_DOCS_SUBJECT = re.compile(r"read-docs\s+`?(?P<subject>[^\s`)]+)")


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

    def test_all_declared_generators_are_importable(self, real_loader):
        """Every generator dotted path must import and resolve to a callable.

        Catches: a generator renamed, moved, or mistyped in the manifest. `DocsLoader`
        swallows the failure into a `⚠️ Generator error` section and still exits 0, so the
        agent silently loses that context — the same silent-injection failure the reference
        checks above guard against.

        The callables are resolved but never invoked, so this stays offline.
        """
        broken = []
        for subject, entry in real_loader.manifest.subjects.items():
            for dotted in entry.generators:
                if dotted.count(":") != 1:
                    broken.append(f"[{subject}] {dotted} — expected the form 'module.path:callable'")
                    continue

                module_path, func_name = dotted.split(":")
                try:
                    module = importlib.import_module(module_path)
                except ImportError as e:
                    broken.append(f"[{subject}] {dotted} — module import failed: {e}")
                    continue

                if not callable(getattr(module, func_name, None)):
                    broken.append(f"[{subject}] {dotted} — '{func_name}' is missing or not callable")

        assert not broken, "Broken generator entries in docs_manifest.yaml:\n" + "\n".join(
            f"  - {b}" for b in broken
        )


class TestBundleSelfConsistency:
    """Validates the *content* of the bundle, not just its file wiring.

    `read-docs` concatenates every reference into a single context, so a prohibition and a
    counter-example are always loaded together. A concrete, runnable command example
    out-weighs an abstract rule, so a doc that forbids a flag must never demonstrate it.
    (This is not hypothetical: the `--status` prohibition once sat 70 lines above an example
    flow that used `--status`, and the flag really does exist on the CLI.)

    The forbidden set is not hardcoded here. Each reference declares its own contract with a
    marker next to the rule, so writing a prohibition and enforcing it stay in one place:

        <!-- forbidden-flags: --status -->
    """

    @pytest.fixture
    def bundle(self):
        """Map every manifest-declared reference to its raw text."""
        loader = DocsLoader()
        ref_root = loader.settings.resolve_references_dir()
        declared = {ref for entry in loader.manifest.subjects.values() for ref in entry.references}
        return {rel: (ref_root / rel).read_text(encoding="utf-8") for rel in sorted(declared)}

    @staticmethod
    def _forbidden_flags(bundle: dict[str, str]) -> set[str]:
        """Collect the flags every bundled reference declares as forbidden."""
        flags: set[str] = set()
        for text in bundle.values():
            for match in _FORBIDDEN_MARKER.finditer(text):
                flags.update(match.group("flags").split())
        return flags

    def test_bundle_declares_its_forbidden_flags(self, bundle):
        """At least one reference must declare a forbidden-flags marker.

        Without this, deleting the marker would silently disable the check below and the
        suite would still pass — a green test that guards nothing.
        """
        assert self._forbidden_flags(bundle), (
            "No `<!-- forbidden-flags: ... -->` marker found in any bundled reference. "
            "If a prohibition was removed on purpose, delete TestBundleSelfConsistency too."
        )

    def test_forbidden_flags_never_appear_in_command_examples(self, bundle):
        """No bundled reference may demonstrate a flag that the bundle forbids.

        Only `wt` *invocations* count as demonstrations. The auto-generated option listings in
        api_spec.md legitimately document `--status`, and the prohibition itself has to name the
        flag to forbid it; neither invokes a command, so neither trips this check.
        """
        forbidden = self._forbidden_flags(bundle)
        violations = []

        for rel_path, text in bundle.items():
            for lineno, line in enumerate(text.splitlines(), 1):
                if "wt " not in line:
                    continue
                for flag in sorted(forbidden):
                    # Match the whole flag only, so `--status` never matches `--status-id`.
                    if re.search(rf"{re.escape(flag)}(?![\w-])", line):
                        violations.append(f"  - {rel_path}:{lineno} demonstrates `{flag}`\n      {line.strip()}")

        assert not violations, (
            "These bundled references demonstrate a flag they also forbid. An agent loading this "
            "context sees a runnable example that contradicts the rule:\n" + "\n".join(violations)
        )


class TestSkillRoutingIntegrity:
    """Closes the last unchecked link in the context chain.

    The chain is SKILL.md -> manifest -> references/generators. The checks above lock the
    manifest to what it points at, but SKILL.md lives outside references/, so nothing
    validates the entry point. Rename a subject in the manifest and SKILL.md keeps routing
    the agent to a subject that no longer exists — `read-docs` then raises KeyError instead
    of loading any context at all.
    """

    @staticmethod
    def _body(text: str) -> str:
        """Drop the YAML frontmatter, keeping only the routing instructions.

        The frontmatter is metadata describing the skill, and its prose spells the argument
        as a bare `subject` placeholder. Only the body actually routes the agent.
        """
        if not text.startswith("---"):
            return text
        _, _, body = text.partition("---")[2].partition("---")
        return body

    def test_every_subject_routed_from_skill_md_exists(self):
        """Every concrete subject cited in SKILL.md must be defined in the manifest."""
        loader = DocsLoader()
        skill_md = loader.settings.resolve_references_dir().parent / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found at {skill_md}"

        cited = set()
        for match in _READ_DOCS_SUBJECT.finditer(self._body(skill_md.read_text(encoding="utf-8"))):
            subject = match.group("subject")
            # `--help` is a flag and `<subject>` is a placeholder; neither is a real subject.
            if subject.startswith(("-", "<")):
                continue
            cited.add(subject)

        assert cited, "SKILL.md cites no concrete subject — its routing instructions are missing."

        unknown = cited - set(loader.list_subjects())
        assert not unknown, (
            "SKILL.md routes the agent to subjects that docs_manifest.yaml does not define:\n"
            + "\n".join(f"  - {s}" for s in sorted(unknown))
            + f"\nDefined subjects: {', '.join(loader.list_subjects())}"
        )
