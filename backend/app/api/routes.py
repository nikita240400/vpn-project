from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas import UserCreate, UserResponse, VPNServer
from backend.app.schemas.marzban import MarzbanUserCreate
from backend.app.services.marzban import MarzbanAPIError, marzban_client

router = APIRouter()


@router.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/servers", response_model=list[VPNServer])
def get_servers() -> list[VPNServer]:
    return [
        VPNServer(
            id=1,
            name="Germany 1",
            country="Germany",
            status="online",
        )
    ]


@router.get("/marzban/users")
def get_marzban_users() -> dict:
    try:
        return marzban_client.get_users()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Marzban request failed: {error}",
        ) from error


@router.post("/marzban/users")
def create_marzban_user(user: MarzbanUserCreate) -> dict:
    expire_at = datetime.now(timezone.utc) + timedelta(days=user.days)
    expire_timestamp = int(expire_at.timestamp())

    data_limit_bytes = (
        user.data_limit_gb * 1024**3
        if user.data_limit_gb is not None
        else 0
    )

    payload = {
        "username": user.username,
        "status": "active",
        "expire": expire_timestamp,
        "data_limit": data_limit_bytes,
        "data_limit_reset_strategy": "no_reset",
        "proxies": {
            "vless": {
                "flow": "",
            }
        },
        "inbounds": {
            "vless": [
                "VLESS TCP REALITY",
            ]
        },
        "note": user.note,
    }

    try:
        return marzban_client.create_user(payload)
    except MarzbanAPIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Marzban request failed: {error}",
        ) from error


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    existing_user = (
        db.query(User)
        .filter(User.telegram_id == user_data.telegram_id)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this telegram_id already exists",
        )

    user = User(
        telegram_id=user_data.telegram_id,
        username=user_data.username,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
