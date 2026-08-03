import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.models.plan import Plan
from backend.app.models.server import Server
from backend.app.models.vpn_subscription import VPNSubscription
from backend.app.models.vpn_subscription_server import VPNSubscriptionServer
from backend.app.services.marzban_provision_service import marzban_provision_service
from backend.app.services.marzban import (
    MarzbanAPIError,
    MarzbanClient,
)
from backend.app.services.qrcode_service import generate_qr_base64


class VPNSubscriptionService:
    def _build_subscription_response(
        self,
        subscription: VPNSubscription,
        servers: list[dict],
        already_exists: bool,
    ) -> dict:
        return {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "expires_at": subscription.expires_at.isoformat(),
            "traffic_limit_bytes": subscription.traffic_limit_bytes,
            "status": subscription.status,
            "already_exists": already_exists,
            "servers": servers,
        }

    def _build_server_response(
        self,
        server: Server,
        marzban_result: dict,
        username: str,
    ) -> dict:
        return {
            "server_id": server.id,
            "username": username,
            "vpn_uuid": marzban_result["vpn_uuid"],
            "link": marzban_result["link"],
            "subscription_url": (marzban_result["subscription_url"]),
            "qr_code": marzban_result["qr_code"],
            "status": marzban_result["status"],
        }

    def _build_connection(
        self,
        subscription: VPNSubscription,
        server: Server,
        username: str,
        marzban_result: dict,
    ) -> VPNSubscriptionServer:
        return VPNSubscriptionServer(
            subscription_id=subscription.id,
            server_id=server.id,
            marzban_username=username,
            vpn_uuid=marzban_result["vpn_uuid"],
            subscription_url=marzban_result["subscription_url"],
            vless_link=marzban_result["link"],
            status=marzban_result["status"],
        )

    def _create_subscription(
        self,
        db: Session,
        user_id: int,
        expires_at: datetime,
        traffic_limit_bytes: int,
    ) -> VPNSubscription:
        subscription = VPNSubscription(
            user_id=user_id,
            expires_at=expires_at,
            traffic_limit_bytes=traffic_limit_bytes,
            status="active",
        )

        db.add(subscription)
        db.flush()

        return subscription

    def _get_active_servers(
        self,
        db: Session,
    ) -> list[Server]:
        return (
            db.query(Server)
            .filter(Server.is_active.is_(True))
            .order_by(Server.priority, Server.id)
            .all()
        )

        if not servers:
            raise ValueError("No active servers found")

        return servers

    def _build_payload(
        self,
        username: str,
        expires_at: datetime,
        traffic_limit_bytes: int,
        note: str | None,
    ) -> dict:
        return {
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

    def _get_active_plan(
        self,
        db: Session,
        plan_id: int,
    ) -> Plan:
        plan = db.get(Plan, plan_id)

        if plan is None:
            raise ValueError("Plan not found")

        if not plan.is_active:
            raise ValueError("Plan is inactive")

        return plan

    def _build_subscription_settings(
        self,
        plan: Plan,
    ) -> tuple[datetime, int]:
        expires_at = datetime.now(timezone.utc) + timedelta(days=plan.days)

        # VPN subscriptions are unlimited by traffic.
        # Access is restricted only by the expiration date.
        traffic_limit_bytes = 0

        return expires_at, traffic_limit_bytes

    def create_subscription(
        self,
        db: Session,
        username: str,
        plan_id: int,
        user_id: int,
        note: str | None,
    ) -> dict:
        plan = self._get_active_plan(
            db=db,
            plan_id=plan_id,
        )

        servers = self._get_active_servers(db)

        if not servers:
            raise ValueError("No active servers found")

        existing_subscription = (
            db.query(VPNSubscription)
            .join(
                VPNSubscriptionServer,
                VPNSubscriptionServer.subscription_id == VPNSubscription.id,
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
                    VPNSubscriptionServer.subscription_id == existing_subscription.id
                )
                .order_by(
                    VPNSubscriptionServer.server_id,
                    VPNSubscriptionServer.id,
                )
                .all()
            )

            return self._build_subscription_response(
                subscription=existing_subscription,
                already_exists=True,
                servers=[
                    {
                        "server_id": connection.server_id,
                        "username": connection.marzban_username,
                        "vpn_uuid": connection.vpn_uuid,
                        "link": connection.vless_link,
                        "subscription_url": (connection.subscription_url),
                        "qr_code": generate_qr_base64(connection.vless_link),
                        "status": connection.status,
                    }
                    for connection in existing_connections
                ],
            )

        expires_at, traffic_limit_bytes = (
            self._build_subscription_settings(plan)
        )

        payload = self._build_payload(
            username=username,
            expires_at=expires_at,
            traffic_limit_bytes=traffic_limit_bytes,
            note=note,
        )

        created_users: list[tuple[MarzbanClient, str]] = []

        try:
            subscription = self._create_subscription(
            db=db,
            user_id=user_id,
            expires_at=expires_at,
            traffic_limit_bytes=traffic_limit_bytes,
        )

            server_results: list[dict] = []

            for server in servers:
                marzban, marzban_result = marzban_provision_service.create_user(
                    server=server,
                    payload=payload,
                )

                created_username = marzban_result["username"]

                created_users.append(
                    (
                        marzban,
                        created_username,
                    )
                )

                connection = self._build_connection(
                    subscription=subscription,
                    server=server,
                    username=created_username,
                    marzban_result=marzban_result,
                )

                db.add(connection)

                server_results.append(
                    self._build_server_response(
                        server=server,
                        marzban_result=marzban_result,
                        username=created_username,
                    )
                )

            db.commit()
            db.refresh(subscription)

            return self._build_subscription_response(
                subscription=subscription,
                already_exists=False,
                servers=server_results,
            )

        except Exception:
            db.rollback()

            marzban_provision_service.rollback_created_users(
                created_users
            )

            raise

    def get_subscription_by_public_token(
        self,
        db: Session,
        public_token: uuid.UUID,
    ) -> VPNSubscription | None:
        return (
            db.query(VPNSubscription)
            .filter(VPNSubscription.public_token == public_token)
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
            .filter(VPNSubscriptionServer.subscription_id == subscription.id)
            .order_by(
                VPNSubscriptionServer.server_id,
                VPNSubscriptionServer.id,
            )
            .all()
        )

        if not connections:
            raise ValueError("Subscription has no server connections")

        now = datetime.now(timezone.utc)
        current_expires_at = subscription.expires_at

        if current_expires_at.tzinfo is None:
            current_expires_at = current_expires_at.replace(tzinfo=timezone.utc)

        old_expires_at = current_expires_at
        base_date = max(current_expires_at, now)
        new_expires_at = base_date + timedelta(days=days)

        modified_users: list[tuple[MarzbanClient, str]] = []
        server_results: list[dict] = []

        try:
            for connection in connections:
                server = db.get(Server, connection.server_id)

                if server is None:
                    raise ValueError(f"Server {connection.server_id} not found")

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

            for marzban, modified_username in reversed(modified_users):
                try:
                    marzban.modify_user(
                        modified_username,
                        {
                            "expire": int(old_expires_at.timestamp()),
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
            .filter(VPNSubscriptionServer.subscription_id == subscription.id)
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
                raise ValueError(f"Server {connection.server_id} not found")

            marzban = MarzbanClient(
                base_url=server.marzban_base_url,
            )

            marzban.delete_user(connection.marzban_username)

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
