import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    domain: str = Field(
        default="/support-ai",
        validation_alias="IMS_DOMAIN",
        description="Domain to identify IMS sessions in the browser",
    )
    cookie_fields: list[str] = Field(
        default=[
            "PHPSESSID",
        ],
        validation_alias="IMS_COOKIE_FIELDS",
        description="Cookie names to retrieve from the browser for authentication (exact match)",
    )
    cookie_prefixes: list[str] = Field(
        default=[
            "wordpress_logged_in",
        ],
        validation_alias="IMS_COOKIE_PREFIXES",
        description="Cookie name prefixes to retrieve from the browser for authentication (prefix match)",
    )


@functools.lru_cache
def get_ims_settings() -> ImsSettings:
    return ImsSettings()  # type: ignore[call-arg]
