import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    base_url: str = Field(validation_alias="IMS_BASE_URL", description="Base URL for the IMS API")


@functools.lru_cache
def get_ims_settings() -> ImsSettings:
    return ImsSettings()  # type: ignore[call-arg]
