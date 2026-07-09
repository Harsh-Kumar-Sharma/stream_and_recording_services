from pydantic import BaseModel, Field


class SessionInfo(BaseModel):
    valid: bool = True
    user_id: str | None = Field(default=None, alias="userId")
    username: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
