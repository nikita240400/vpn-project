from pydantic import BaseModel, Field


class MarzbanUserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-z0-9_]+$",
    )
    days: int = Field(default=30, ge=1, le=365)
    data_limit_gb: int | None = Field(default=None, ge=1)
    note: str | None = None
