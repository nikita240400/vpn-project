from pydantic import BaseModel, Field


class ServerCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    country: str = Field(
        min_length=2,
        max_length=100,
    )
    city: str | None = Field(
        default=None,
        max_length=100,
    )
    host: str = Field(
        min_length=3,
        max_length=255,
    )
    port: int = Field(
        default=443,
        ge=1,
        le=65535,
    )
    marzban_base_url: str = Field(
        min_length=8,
        max_length=255,
    )
    is_active: bool = True
    priority: int = Field(
        default=100,
        ge=0,
    )


class ServerUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    city: str | None = Field(
        default=None,
        max_length=100,
    )
    host: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )
    port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )
    marzban_base_url: str | None = Field(
        default=None,
        min_length=8,
        max_length=255,
    )
    is_active: bool | None = None
    priority: int | None = Field(
        default=None,
        ge=0,
    )