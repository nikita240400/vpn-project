from pydantic import BaseModel, ConfigDict


class VPNServer(BaseModel):
    id: int
    name: str
    country: str
    status: str


class UserCreate(BaseModel):
    telegram_id: str
    username: str | None = None


class UserResponse(UserCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
