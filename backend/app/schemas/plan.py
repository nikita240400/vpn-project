from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    price: int = Field(ge=0)
    days: int = Field(ge=1, le=3650)
    traffic_limit_gb: int | None = Field(
        default=None,
        ge=1,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    is_active: bool = True

class PlanUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    price: int | None = Field(
        default=None,
        ge=0,
    )
    days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )
    traffic_limit_gb: int | None = Field(
        default=None,
        ge=1,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    is_active: bool | None = None