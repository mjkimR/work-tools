import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SlackSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    bot_token: str = Field(
        validation_alias="SLACK_BOT_TOKEN",
        description="Slack Bot Token (xoxb-...)",
    )
    default_channel: str = Field(
        default="",
        validation_alias="SLACK_DEFAULT_CHANNEL",
        description="Default channel ID to post messages to (e.g. C01234567)",
    )


@functools.lru_cache
def get_slack_settings() -> SlackSettings:
    return SlackSettings()  # type: ignore[call-arg]
