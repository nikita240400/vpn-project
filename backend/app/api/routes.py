import uuid
from urllib.parse import quote
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.server import Server
from backend.app.models.plan import Plan
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
    PlanCreate,
    PlanUpdate,
    ServerCreate,
    ServerUpdate,
    TokenResponse,
    UserCreate,
    UserResponse,
    VPNServer,
)

from backend.app.schemas.marzban import (
    MarzbanUserCreate,
    SubscriptionExtend,
)

from backend.app.services.server_service import server_service

from backend.app.services.vpn_subscription_service import (
    vpn_subscription_service,
)

router = APIRouter()

@router.get("/plans")
def get_plans(
    db: Session = Depends(get_db),
) -> list[dict]:
    plans = (
        db.query(Plan)
        .filter(Plan.is_active.is_(True))
        .order_by(Plan.days.asc())
        .all()
    )

    return [
        {
            "id": plan.id,
            "name": plan.name,
            "price": plan.price,
            "days": plan.days,
            "traffic_limit_gb": plan.traffic_limit_gb,
            "description": plan.description,
            "is_active": plan.is_active,
        }
        for plan in plans
    ]

@router.post("/admin/plans", status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
) -> dict:
    existing_plan = (
        db.query(Plan)
        .filter(
            (Plan.name == data.name)
            | (Plan.days == data.days)
        )
        .first()
    )

    if existing_plan is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plan with this name or duration already exists",
        )

    plan = Plan(
        name=data.name,
        price=data.price,
        days=data.days,
        traffic_limit_gb=data.traffic_limit_gb,
        description=data.description,
        is_active=data.is_active,
    )

    db.add(plan)

    try:
        db.commit()
        db.refresh(plan)
    except Exception:
        db.rollback()
        raise

    return {
        "id": plan.id,
        "name": plan.name,
        "price": plan.price,
        "days": plan.days,
        "traffic_limit_gb": plan.traffic_limit_gb,
        "description": plan.description,
        "is_active": plan.is_active,
    }

@router.put("/admin/plans/{plan_id}")
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    db: Session = Depends(get_db),
) -> dict:
    plan = db.get(Plan, plan_id)

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        duplicate_name = (
            db.query(Plan)
            .filter(
                Plan.name == update_data["name"],
                Plan.id != plan_id,
            )
            .first()
        )

        if duplicate_name is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plan with this name already exists",
            )

    if "days" in update_data:
        duplicate_days = (
            db.query(Plan)
            .filter(
                Plan.days == update_data["days"],
                Plan.id != plan_id,
            )
            .first()
        )

        if duplicate_days is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plan with this duration already exists",
            )

    for field, value in update_data.items():
        setattr(plan, field, value)

    try:
        db.commit()
        db.refresh(plan)
    except Exception:
        db.rollback()
        raise

    return {
        "id": plan.id,
        "name": plan.name,
        "price": plan.price,
        "days": plan.days,
        "traffic_limit_gb": plan.traffic_limit_gb,
        "description": plan.description,
        "is_active": plan.is_active,
    }

@router.get("/")

@router.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}

@router.post(
    "/admin/servers",
    status_code=status.HTTP_201_CREATED,
)
def create_server(
    data: ServerCreate,
    db: Session = Depends(get_db),
) -> dict:
    existing_server = (
        db.query(Server)
        .filter(
            (Server.name == data.name)
            | (Server.host == data.host)
        )
        .first()
    )

    if existing_server is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server with this name or host already exists",
        )

    server = server_service.create(
        db=db,
        data=data.model_dump(),
    )

    return {
        "id": server.id,
        "name": server.name,
        "country": server.country,
        "city": server.city,
        "host": server.host,
        "port": server.port,
        "marzban_base_url": server.marzban_base_url,
        "is_active": server.is_active,
        "priority": server.priority,
    }

@router.get("/servers", response_model=list[VPNServer])
def get_servers(
    db: Session = Depends(get_db),
) -> list[VPNServer]:
    servers = server_service.get_all(db)

    return [
        VPNServer(
            id=server.id,
            name=server.name,
            country=server.country,
            status="online" if server.is_active else "offline",
        )
        for server in servers
    ]

@router.put("/admin/servers/{server_id}")
def update_server(
    server_id: int,
    data: ServerUpdate,
    db: Session = Depends(get_db),
) -> dict:
    server = db.get(Server, server_id)

    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        duplicate_name = (
            db.query(Server)
            .filter(
                Server.name == update_data["name"],
                Server.id != server_id,
            )
            .first()
        )

        if duplicate_name is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Server with this name already exists",
            )

    if "host" in update_data:
        duplicate_host = (
            db.query(Server)
            .filter(
                Server.host == update_data["host"],
                Server.id != server_id,
            )
            .first()
        )

        if duplicate_host is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Server with this host already exists",
            )

    server = server_service.update(
        db=db,
        server=server,
        data=update_data,
    )

    return {
        "id": server.id,
        "name": server.name,
        "country": server.country,
        "city": server.city,
        "host": server.host,
        "port": server.port,
        "marzban_base_url": server.marzban_base_url,
        "is_active": server.is_active,
        "priority": server.priority,
    }

@router.delete(
    "/admin/servers/{server_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
) -> None:
    server = db.get(Server, server_id)

    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    server_service.delete(
        db=db,
        server=server,
    )

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
	    plan_id=user.plan_id,
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

def serialize_subscription(
    subscription: VPNSubscription,
) -> dict:
    connections = sorted(
        subscription.server_connections,
        key=lambda item: (
            item.server_id,
            item.id,
        ),
    )

    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "expires_at": subscription.expires_at.isoformat(),
        "traffic_limit_bytes": (
            subscription.traffic_limit_bytes
        ),
        "status": subscription.status,
        "created_at": subscription.created_at.isoformat(),
        "servers": [
            {
                "server_id": connection.server_id,
                "username": connection.marzban_username,
                "vpn_uuid": connection.vpn_uuid,
                "vless_link": connection.vless_link,
                "subscription_url": (
                    connection.subscription_url
                ),
                "status": connection.status,
            }
            for connection in connections
        ],
    }


@router.get("/users/{user_id}/subscriptions")
def get_user_subscriptions(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    user = db.get(User, user_id)

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
        serialize_subscription(subscription)
        for subscription in subscriptions
    ]


@router.get("/subscriptions/{subscription_id}/qr")
def get_subscription_qr(
    subscription_id: int,
    db: Session = Depends(get_db),
) -> dict:
    subscription = db.get(
        VPNSubscription,
        subscription_id,
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    connections = sorted(
        subscription.server_connections,
        key=lambda item: (
            item.server_id,
            item.id,
        ),
    )

    return {
        "subscription_id": subscription.id,
        "servers": [
            {
                "server_id": connection.server_id,
                "username": connection.marzban_username,
                "qr_code": generate_qr_base64(
                    connection.vless_link
                ),
            }
            for connection in connections
        ],
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
        or not verify_password(
            data.password,
            user.password_hash,
        )
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
        .filter(
            VPNSubscription.user_id == current_user.id
        )
        .order_by(VPNSubscription.id.desc())
        .all()
    )

    return [
        {
            **serialize_subscription(subscription),
            "public_token": str(subscription.public_token),
        }
        for subscription in subscriptions
    ]


@router.get(
    "/sub/{public_token}",
    response_class=PlainTextResponse,
)
def get_subscription(
    public_token: uuid.UUID,
    db: Session = Depends(get_db),
):
    subscription = (
        vpn_subscription_service
        .get_subscription_by_public_token(
            db=db,
            public_token=public_token,
        )
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    connections = sorted(
        (
            connection
            for connection in subscription.server_connections
            if connection.status == "active"
            and connection.vless_link
            and connection.server is not None
        ),
        key=lambda connection: (
            connection.server.priority,
            connection.server_id,
            connection.id,
        ),
    )

    links = []

    for connection in connections:
        link_without_old_name = (
            connection.vless_link.split("#", 1)[0]
        )
        server_name = quote(
            connection.server.name,
            safe="",
        )
        links.append(
            f"{link_without_old_name}#{server_name}"
        )

    if not links:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    expires_at = subscription.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc,
        )

    expire_timestamp = int(expires_at.timestamp())
    traffic_limit = int(
        subscription.traffic_limit_bytes or 0
    )

    metadata = [
        "#profile-title: Напальчник VPN",
        "#profile-update-interval: 1",
        (
            "#subscription-userinfo: "
            f"upload=0; download=0; "
            f"total={traffic_limit}; "
            f"expire={expire_timestamp}"
        ),
        "#announce: Натяни по глубже",
    ]

    return "\n".join(metadata + links)


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
            plan_id=data.plan_id,
            note=data.note,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except MarzbanAPIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Subscription creation failed: {error}"
            ),
        ) from error

