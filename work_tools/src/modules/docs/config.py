import functools
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DocsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    references_dir: str = Field(
        default="work_tools/references",
        validation_alias="DOCS_REFERENCES_DIR",
        description="Project-root-relative path to the references directory",
    )
    manifest_path: str = Field(
        default="work_tools/src/modules/docs/docs_manifest.yaml",
        validation_alias="DOCS_MANIFEST_PATH",
        description="Project-root-relative path to docs_manifest.yaml",
    )

    def resolve_references_dir(self, project_root: str | Path) -> Path:
        """Resolve the references directory as an absolute path."""
        return Path(project_root) / self.references_dir

    def resolve_manifest_path(self, project_root: str | Path) -> Path:
        """Resolve the manifest file as an absolute path."""
        return Path(project_root) / self.manifest_path


@functools.lru_cache
def get_docs_settings() -> DocsSettings:
    return DocsSettings()  # type: ignore[call-arg]
