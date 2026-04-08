from pydantic import BaseModel


class SessionInfo(BaseModel):
    base_url: str
    tab_url: str
    local_storage: dict[str, str | None] = {}
    cookies: dict[str, str | None] = {}
