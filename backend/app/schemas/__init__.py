from pydantic import BaseModel, ConfigDict


class VPNServer(BaseModel):
    id: int
    name: str
    country: str
    status: str


class UserCreate(BaseModel):
    telegram_id: str
    username: str | None = None
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: str
    username: str | None = None

class LoginRequest(BaseModel):
    telegram_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

from backend.app.schemas.marzban import (
    MarzbanUserCreate,
    MySubscriptionCreate,
    SubscriptionExtend,
)