import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitRepoSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    user_email: str = Field(validation_alias="GIT_USER_EMAIL", description="Git user email for filtering commits")
    path: str = Field(validation_alias="GIT_TARGET_REPO", description="Target Git repository path for operations")


@functools.lru_cache
def get_git_settings() -> GitRepoSettings:
    return GitRepoSettings()  # type: ignore[call-arg]
