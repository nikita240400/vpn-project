from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.services.marzban import MarzbanAPIError, marzban_client
from backend.app.models.vpn_subscription import VPNSubscription
from backend.app.services.qrcode_service import generate_qr_base64
from backend.app.core.security import hash_password, verify_password
from backend.app.core.auth import create_access_token
from backend.app.core.dependencies import get_current_user
from backend.app.schemas import (
    LoginRequest,
    MySubscriptionCreate,
    TokenResponse,
    UserCreate,
    UserResponse,
    VPNServer,
)

from backend.app.schemas.marzban import (
    MarzbanUserCreate,
    SubscriptionExtend,
)

from backend.app.services.vpn_subscription_service import (
    vpn_subscription_service,
)

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
def create_marzban_user(
    user: MarzbanUserCreate,
    db: Session = Depends(get_db),
) -> dict:
    existing_user = db.query(User).filter(User.id == user.user_id).first()

    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        return vpn_subscription_service.create_subscription(
            db=db,
            user_id=user.user_id,
            username=user.username,
            days=user.days,
            traffic_gb=user.data_limit_gb,
            note=user.note,
        )
    except MarzbanAPIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription creation failed: {error}",
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
        password_hash=hash_password(user_data.password),
        )  

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/users/{user_id}/subscriptions")
def get_user_subscriptions(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    subscriptions = (
        db.query(VPNSubscription)
        .filter(VPNSubscription.user_id == user_id)
        .order_by(VPNSubscription.id.desc())
        .all()
    )

    return [
        {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "username": subscription.marzban_username,
            "vpn_uuid": subscription.vpn_uuid,
            "vless_link": subscription.vless_link,
            "subscription_url": subscription.subscription_url,
            "expires_at": subscription.expires_at.isoformat(),
            "traffic_limit_bytes": subscription.traffic_limit_bytes,
            "status": subscription.status,
            "created_at": subscription.created_at.isoformat(),
        }
        for subscription in subscriptions
    ]

    @router.get("/users/{user_id}/subscriptions")
    def get_user_subscriptions(
            user_id: int,
            db: Session = Depends(get_db),
    )  -> list[dict]:
        user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    subscriptions = (
        db.query(VPNSubscription)
        .filter(VPNSubscription.user_id == user_id)
        .order_by(VPNSubscription.id.desc())
        .all()
    )

    return [
        {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "username": subscription.marzban_username,
            "vpn_uuid": subscription.vpn_uuid,
            "vless_link": subscription.vless_link,
            "subscription_url": subscription.subscription_url,
            "expires_at": subscription.expires_at.isoformat(),
            "traffic_limit_bytes": subscription.traffic_limit_bytes,
            "status": subscription.status,
            "created_at": subscription.created_at.isoformat(),
        }
        for subscription in subscriptions
    ]

    @router.get("/subscriptions/{subscription_id}/qr")
    def get_subscription_qr(
    subscription_id: int,
    db: Session = Depends(get_db),
) -> dict:
        subscription = (
        db.query(VPNSubscription)
        .filter(VPNSubscription.id == subscription_id)
        .first()
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    return {
        "subscription_id": subscription.id,
        "username": subscription.marzban_username,
        "qr_code": generate_qr_base64(subscription.vless_link),
    }


@router.patch("/subscriptions/{subscription_id}/extend")
def extend_subscription(
    subscription_id: int,
    data: SubscriptionExtend,
    db: Session = Depends(get_db),
) -> dict:
    try:
        return vpn_subscription_service.extend_subscription(
            db=db,
            subscription_id=subscription_id,
            days=data.days,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except MarzbanAPIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error


@router.delete("/subscriptions/{subscription_id}")
def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
) -> dict:
    try:
        return vpn_subscription_service.delete_subscription(
            db=db,
            subscription_id=subscription_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except MarzbanAPIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = (
        db.query(User)
        .filter(User.telegram_id == data.telegram_id)
        .first()
    )

    if (
        user is None
        or user.password_hash is None
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )
    return TokenResponse(
    access_token=token,
    token_type="bearer",
)

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "id": current_user.id,
        "telegram_id": current_user.telegram_id,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat(),
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

@router.get("/me/subscriptions")
def get_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    subscriptions = (
        db.query(VPNSubscription)
        .filter(VPNSubscription.user_id == current_user.id)
        .order_by(VPNSubscription.id.desc())
        .all()
    )

    return [
        {
            "id": subscription.id,
            "username": subscription.marzban_username,
            "vpn_uuid": subscription.vpn_uuid,
            "vless_link": subscription.vless_link,
            "subscription_url": subscription.subscription_url,
            "expires_at": subscription.expires_at.isoformat(),
            "traffic_limit_bytes": subscription.traffic_limit_bytes,
            "status": subscription.status,
            "created_at": subscription.created_at.isoformat(),
        }
        for subscription in subscriptions
    ]
@router.post("/me/subscriptions")
def create_my_subscription(
    data: MySubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return vpn_subscription_service.create_subscription(
            db=db,
            user_id=current_user.id,
            username=data.username,
            days=data.days,
            traffic_gb=data.data_limit_gb,
            note=data.note,
        )
    except MarzbanAPIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription creation failed: {error}",
        ) from error