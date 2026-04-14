"""Docs manifest loader — parses docs_manifest.yaml and composes context output."""

from __future__ import annotations

import importlib
import os

import yaml
from pydantic import BaseModel

from modules.docs.config import DocsSettings, get_docs_settings

# ── Manifest Schema ──────────────────────────────────────────────────────────


class ManifestSubject(BaseModel):
    """Schema for a single subject entry in docs_manifest.yaml."""

    description: str = ""
    references: list[str] = []
    env_vars: list[str] = []
    generators: list[str] = []


class DocsManifest(BaseModel):
    """Top-level schema for docs_manifest.yaml."""

    subjects: dict[str, ManifestSubject] = {}


# ── Sensitive Env-Var Patterns ───────────────────────────────────────────────

_SENSITIVE_KEYWORDS = ("TOKEN", "SECRET", "PASSWORD", "KEY", "CREDENTIAL")


def _mask_value(key: str, value: str) -> str:
    """Mask environment variable values whose key contains sensitive keywords."""
    upper = key.upper()
    if any(kw in upper for kw in _SENSITIVE_KEYWORDS):
        if len(value) <= 4:
            return "***"
        return value[:2] + "***" + value[-2:]
    return value


# ── Loader ───────────────────────────────────────────────────────────────────


class DocsLoader:
    """Loads and composes context documents from the docs manifest.

    Reads docs_manifest.yaml, resolves file paths relative to the project root,
    collects environment variables, runs dynamic generators, and produces a
    Markdown string suitable for AI consumption.
    """

    def __init__(self, settings: DocsSettings | None = None):
        """Initialize DocsLoader with settings and parse the manifest."""
        self.settings: DocsSettings = settings or get_docs_settings()
        self.manifest = self._load_manifest()

    # ── Public API ────────────────────────────────────────────────────────

    def list_subjects(self) -> list[str]:
        """Return a sorted list of available subject names."""
        return sorted(self.manifest.subjects.keys())

    def list_subjects_with_descriptions(self) -> dict[str, str]:
        """Return an ordered dict of subject name -> first line of description."""
        return {
            name: (entry.description.strip().splitlines()[0] if entry.description else "")
            for name, entry in sorted(self.manifest.subjects.items())
        }

    def load(self, subject: str) -> str:
        """Compose the full context document for a given subject.

        Args:
            subject: The subject key defined in docs_manifest.yaml.

        Returns:
            A Markdown-formatted string combining references, env vars, and generated data.

        Raises:
            KeyError: If the subject is not found in the manifest.
        """
        entry = self.manifest.subjects.get(subject)
        if entry is None:
            available = ", ".join(self.list_subjects()) or "(none)"
            raise KeyError(f"Subject '{subject}' not found. Available subjects: {available}")

        sections: list[str] = []

        # Header
        sections.append(f"# Context: {subject}")
        if entry.description:
            sections.append(entry.description.strip())

        # References
        for ref_section in self._read_references(entry.references):
            sections.append(ref_section)

        # Environment Variables
        if entry.env_vars:
            sections.append(self._collect_env_vars(entry.env_vars))

        # Dynamic Generators
        for gen_section in self._run_generators(entry.generators):
            sections.append(gen_section)

        return "\n\n".join(sections) + "\n"

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _load_manifest(self) -> DocsManifest:
        """Parse docs_manifest.yaml into a DocsManifest model."""
        manifest_path = self.settings.resolve_manifest_path()
        with open(manifest_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return DocsManifest.model_validate(raw)

    def _read_references(self, paths: list[str]) -> list[str]:
        """Read reference files and return Markdown sections."""
        sections: list[str] = []
        ref_root = self.settings.resolve_references_dir()
        for rel_path in paths:
            abs_path = ref_root / rel_path
            if not abs_path.exists():
                sections.append(f"## 📄 {rel_path}\n\n> ⚠️ File not found: `{abs_path}`")
                continue
            content = abs_path.read_text(encoding="utf-8").strip()
            sections.append(f"## 📄 {rel_path}\n\n{content}")
        return sections

    def _collect_env_vars(self, keys: list[str]) -> str:
        """Collect environment variables into a Markdown list."""
        lines = ["## 🔧 Environment", ""]
        for key in keys:
            value = os.environ.get(key)
            if value is None:
                lines.append(f"- `{key}`: `<NOT SET>`")
            else:
                masked = _mask_value(key, value)
                lines.append(f"- `{key}`: `{masked}`")
        return "\n".join(lines)

    def _run_generators(self, callables: list[str]) -> list[str]:
        """Dynamically import and run generator callables.

        Each entry is a dotted path in the form 'module.path:callable_name'.
        The callable must accept no arguments and return a string.
        """
        sections: list[str] = []
        for dotted in callables:
            name = dotted
            try:
                module_path, func_name = dotted.rsplit(":", 1)
                mod = importlib.import_module(module_path)
                func = getattr(mod, func_name)
                result = func()
                sections.append(f"## ⚙️ Dynamic: {name}\n\n{str(result).strip()}")
            except Exception as e:
                sections.append(f"## ⚙️ Dynamic: {name}\n\n> ⚠️ Generator error: `{e}`")
        return sections
