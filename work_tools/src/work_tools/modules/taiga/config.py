import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TaigaSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    project_id: int | None = Field(
        default=None, validation_alias="TAIGA_PROJECT_ID", description="Default project ID to work with in Taiga"
    )
    domain: str = Field(
        default="taiga", validation_alias="TAIGA_DOMAIN", description="Domain to identify Taiga sessions in the browser"
    )


@functools.lru_cache
def get_taiga_settings() -> TaigaSettings:
    return TaigaSettings()  # type: ignore[call-arg]
