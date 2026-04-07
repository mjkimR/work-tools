import functools
import os

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TaigaSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    project_id: int | None = Field(
        default=None, validation_alias="TAIGA_PROJECT_ID", description="Default project ID to work with in Taiga"
    )
    domain: str = Field(
        default="taiga", validation_alias="TAIGA_DOMAIN", description="Domain to identify Taiga sessions in the browser"
    )
    custom_attributes: dict[str, int] = Field(
        default={},
        validation_alias="TAIGA_CA",
        description="Custom attributes for user stories, loaded from TAIGA_CA_* environment variables",
    )

    @model_validator(mode="before")
    @classmethod
    def parse_ca_fields(cls, values: dict) -> dict:
        """TAIGA_CA_* 환경변수를 TAIGA_CA dict로 합칩니다."""
        # values에 없는 경우 os.environ에서도 탐색
        all_values = {**os.environ, **values}
        print(all_values)
        ca: dict[str, int] = {}
        for k, v in all_values.items():
            if k.startswith("TAIGA_CA_"):
                key = k.removeprefix("TAIGA_CA_")
                ca[key] = int(v)
        values["custom_attributes"] = ca
        return values


@functools.lru_cache
def get_taiga_settings() -> TaigaSettings:
    return TaigaSettings()  # type: ignore[call-arg]
