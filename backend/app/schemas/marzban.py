from pydantic import BaseModel, Field


class MarzbanUserCreate(BaseModel):
    user_id: int = Field(ge=1)
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-z0-9_]+$",
    )
    plan_id: int = Field(ge=1)
    note: str | None = None

class MySubscriptionCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-z0-9_]+$",
    )
    plan_id: int = Field(ge=1)
    note: str | None = None

class SubscriptionExtend(BaseModel):
    days: int = Field(
        ge=1,
        le=365,
        description="Количество дней для продления",
    )