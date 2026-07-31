import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.models.plan import Plan
from backend.app.models.server import Server
from backend.app.models.vpn_subscription import VPNSubscription
from backend.app.models.vpn_subscription_server import VPNSubscriptionServer
from backend.app.services.marzban import (
    MarzbanAPIError,
    MarzbanClient,
)
from backend.app.services.qrcode_service import generate_qr_base64


class VPNSubscriptionService:
    def create_subscription(
        self,
        db: Session,
        username: str,
        plan_id: int,
        user_id: int,
        note: str | None,
    ) -> dict:
        plan = db.get(Plan, plan_id)

        if plan is None:
            raise ValueError("Plan not found")

        if not plan.is_active:
            raise ValueError("Plan is inactive")

        servers = (
            db.query(Server)
            .filter(Server.is_active.is_(True))
            .order_by(Server.priority, Server.id)
            .all()
        )

        if not servers:
            raise ValueError("No active servers found")

        existing_subscription = (
            db.query(VPNSubscription)
            .join(
                VPNSubscriptionServer,
                VPNSubscriptionServer.subscription_id
                == VPNSubscription.id,
            )
            .filter(
                VPNSubscription.user_id == user_id,
                VPNSubscriptionServer.marzban_username == username,
            )
            .first()
        )

        if existing_subscription is not None:
            existing_connections = (
                db.query(VPNSubscriptionServer)
                .filter(
                    VPNSubscriptionServer.subscription_id
                    == existing_subscription.id
                )
                .order_by(
                    VPNSubscriptionServer.server_id,
                    VPNSubscriptionServer.id,
                )
                .all()
            )

            return {
                "id": existing_subscription.id,
                "user_id": existing_subscription.user_id,
                "expires_at": (
                    existing_subscription.expires_at.isoformat()
                ),
                "traffic_limit_bytes": (
                    existing_subscription.traffic_limit_bytes
                ),
                "status": existing_subscription.status,
                "already_exists": True,
                "servers": [
                    {
                        "server_id": connection.server_id,
                        "username": connection.marzban_username,
                        "vpn_uuid": connection.vpn_uuid,
                        "link": connection.vless_link,
                        "subscription_url": (
                            connection.subscription_url
                        ),
                        "qr_code": generate_qr_base64(
                            connection.vless_link
                        ),
                        "status": connection.status,
                    }
                    for connection in existing_connections
                ],
            }

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=plan.days
        )

        traffic_limit_bytes = (
            plan.traffic_limit_gb * 1024**3
            if plan.traffic_limit_gb is not None
            else 0
        )

        payload = {
            "username": username,
            "status": "active",
            "expire": int(expires_at.timestamp()),
            "data_limit": traffic_limit_bytes,
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
            "note": note,
        }

        created_users: list[tuple[MarzbanClient, str]] = []

        try:
            subscription = VPNSubscription(
                user_id=user_id,
                expires_at=expires_at,
                traffic_limit_bytes=traffic_limit_bytes,
                status="active",
            )

            db.add(subscription)
            db.flush()

            server_results: list[dict] = []

            for server in servers:
                marzban = MarzbanClient(
                    base_url=server.marzban_base_url,
                )

                try:
                    marzban_result = marzban.create_user(payload)
                except MarzbanAPIError as error:
                    if error.status_code == 409:
                        raise ValueError(
                            "User already exists in Marzban "
                            f"on server {server.id}, but the "
                            "subscription is missing in the "
                            "backend database"
                        ) from error

                    raise

                created_username = marzban_result["username"]

                created_users.append(
                    (
                        marzban,
                        created_username,
                    )
                )

                connection = VPNSubscriptionServer(
                    subscription_id=subscription.id,
                    server_id=server.id,
                    marzban_username=created_username,
                    vpn_uuid=marzban_result["vpn_uuid"],
                    subscription_url=(
                        marzban_result["subscription_url"]
                    ),
                    vless_link=marzban_result["link"],
                    status=marzban_result["status"],
                )

                db.add(connection)

                server_results.append(
                    {
                        "server_id": server.id,
                        "username": created_username,
                        "vpn_uuid": marzban_result["vpn_uuid"],
                        "link": marzban_result["link"],
                        "subscription_url": (
                            marzban_result["subscription_url"]
                        ),
                        "qr_code": marzban_result["qr_code"],
                        "status": marzban_result["status"],
                    }
                )

            db.commit()
            db.refresh(subscription)

            return {
                "id": subscription.id,
                "user_id": subscription.user_id,
                "expires_at": subscription.expires_at.isoformat(),
                "traffic_limit_bytes": (
                    subscription.traffic_limit_bytes
                ),
                "status": subscription.status,
                "already_exists": False,
                "servers": server_results,
            }

        except Exception:
            db.rollback()

            for marzban, created_username in reversed(created_users):
                try:
                    marzban.delete_user(created_username)
                except MarzbanAPIError:
                    pass

            raise

    def get_subscription_by_public_token(
        self,
        db: Session,
        public_token: uuid.UUID,
    ) -> VPNSubscription | None:
        return (
            db.query(VPNSubscription)
            .filter(
                VPNSubscription.public_token == public_token
            )
            .first()
        )
            
    def extend_subscription(
        self,
        db: Session,
        subscription_id: int,
        days: int,
    ) -> dict:
        subscription = db.get(VPNSubscription, subscription_id)

        if subscription is None:
            raise ValueError("Subscription not found")

        connections = (
            db.query(VPNSubscriptionServer)
            .filter(
                VPNSubscriptionServer.subscription_id
                == subscription.id
            )
            .order_by(
                VPNSubscriptionServer.server_id,
                VPNSubscriptionServer.id,
            )
            .all()
        )

        if not connections:
            raise ValueError(
                "Subscription has no server connections"
            )

        now = datetime.now(timezone.utc)
        current_expires_at = subscription.expires_at

        if current_expires_at.tzinfo is None:
            current_expires_at = current_expires_at.replace(
tzinfo=timezone.utc
            )

        old_expires_at = current_expires_at
        base_date = max(current_expires_at, now)
        new_expires_at = base_date + timedelta(days=days)

        modified_users: list[tuple[MarzbanClient, str]] = []
        server_results: list[dict] = []

        try:
            for connection in connections:
                server = db.get(Server, connection.server_id)

                if server is None:
                    raise ValueError(
                        f"Server {connection.server_id} not found"
                    )

                marzban = MarzbanClient(
                    base_url=server.marzban_base_url,
                )

                marzban_result = marzban.modify_user(
                    connection.marzban_username,
                    {
                        "expire": int(new_expires_at.timestamp()),
                    },
                )

                modified_users.append(
                    (
                        marzban,
                        connection.marzban_username,
                    )
                )

                connection.status = marzban_result.get(
                    "status",
                    connection.status,
                )

                server_results.append(
                    {
                        "server_id": connection.server_id,
                        "username": connection.marzban_username,
                        "status": connection.status,
                    }
                )

            subscription.expires_at = new_expires_at
            subscription.status = "active"

            db.commit()
            db.refresh(subscription)

            return {
                "id": subscription.id,
                "user_id": subscription.user_id,
                "expires_at": subscription.expires_at.isoformat(),
                "status": subscription.status,
                "extended_by_days": days,
                "servers": server_results,
            }

        except Exception:
            db.rollback()

            for marzban, modified_username in reversed(
                modified_users
            ):
                try:
                    marzban.modify_user(
                        modified_username,
                        {
                            "expire": int(
                                old_expires_at.timestamp()
                            ),
                        },
                    )
                except Exception:
                    pass

            raise

    def delete_subscription(
        self,
        db: Session,
        subscription_id: int,
    ) -> dict:
        subscription = db.get(VPNSubscription, subscription_id)

        if subscription is None:
            raise ValueError("Subscription not found")

        connections = (
            db.query(VPNSubscriptionServer)
            .filter(
                VPNSubscriptionServer.subscription_id
                == subscription.id
            )
            .order_by(
                VPNSubscriptionServer.server_id,
                VPNSubscriptionServer.id,
            )
            .all()
        )

        deleted_servers: list[dict] = []

        for connection in connections:
            server = db.get(Server, connection.server_id)

            if server is None:
                raise ValueError(
                    f"Server {connection.server_id} not found"
                )

            marzban = MarzbanClient(
                base_url=server.marzban_base_url,
            )

            marzban.delete_user(
                connection.marzban_username
            )

            deleted_servers.append(
                {
                    "server_id": connection.server_id,
                    "username": connection.marzban_username,
                }
            )

        try:
            db.delete(subscription)
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "deleted": True,
"subscription_id": subscription_id,
            "servers": deleted_servers,
        }


vpn_subscription_service = VPNSubscriptionService()