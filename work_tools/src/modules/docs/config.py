import functools
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_FILE_DIR = Path(__file__).parent
_MAIN_DIR = _FILE_DIR.parent.parent.parent


class DocsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    references_dir: str = Field(
        default=str(_MAIN_DIR / "references"),
        validation_alias="DOCS_REFERENCES_DIR",
        description="Project-root-relative path to the references directory",
    )
    manifest_path: str = Field(
        default=str(_FILE_DIR / "docs_manifest.yaml"),
        validation_alias="DOCS_MANIFEST_PATH",
        description="Project-root-relative path to docs_manifest.yaml",
    )

    def resolve_references_dir(self) -> Path:
        """Resolve the references directory as an absolute path."""
        path = Path(self.references_dir)
        if not path.is_absolute():
            path = _MAIN_DIR / path
        if not path.exists():
            raise FileNotFoundError(f"References directory not found at resolved path: {path}")
        return path

    def resolve_manifest_path(self) -> Path:
        """Resolve the manifest file as an absolute path."""
        path = Path(self.manifest_path)
        if not path.is_absolute():
            path = _MAIN_DIR / path
        if not path.exists():
            raise FileNotFoundError(f"Docs manifest file not found at resolved path: {path}")
        return path


@functools.lru_cache
def get_docs_settings() -> DocsSettings:
    return DocsSettings()  # type: ignore[call-arg]
