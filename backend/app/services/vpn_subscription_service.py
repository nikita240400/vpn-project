from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.models.vpn_subscription import VPNSubscription
from backend.app.services.marzban import (
    MarzbanAPIError,
    marzban_client,
)


class VPNSubscriptionService:
    def __init__(self) -> None:
        self.marzban = marzban_client

    def create_subscription(
        self,
        db: Session,
        user_id: int,
        username: str,
        days: int,
        traffic_gb: int | None,
        note: str | None,
    ) -> dict:
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)

        traffic_limit_bytes = (
            traffic_gb * 1024**3
            if traffic_gb is not None
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

        marzban_user_created = False

        try:
            marzban_result = self.marzban.create_user(payload)
            marzban_user_created = True

            subscription = VPNSubscription(
                user_id=user_id,
                marzban_username=marzban_result["username"],
                vpn_uuid=marzban_result["vpn_uuid"],
                subscription_url=marzban_result["subscription_url"],
                vless_link=marzban_result["link"],
                expires_at=expires_at,
                traffic_limit_bytes=traffic_limit_bytes,
                status=marzban_result["status"],
            )

            db.add(subscription)
            db.commit()
            db.refresh(subscription)

            return {
                "id": subscription.id,
                "user_id": subscription.user_id,
                "username": subscription.marzban_username,
                "vpn_uuid": subscription.vpn_uuid,
                "link": subscription.vless_link,
                "subscription_url": subscription.subscription_url,
                "qr_code": marzban_result["qr_code"],
                "expires_at": subscription.expires_at.isoformat(),
                "traffic_limit_bytes": subscription.traffic_limit_bytes,
                "status": subscription.status,
            }

        except Exception:
            db.rollback()

            if marzban_user_created:
                try:
                    self.marzban.delete_user(username)
                except MarzbanAPIError:
                    pass

            raise

    def extend_subscription(
        self,
        db: Session,
        subscription_id: int,
        days: int,
    ) -> dict:
        subscription = (
            db.query(VPNSubscription)
            .filter(VPNSubscription.id == subscription_id)
            .first()
        )

        if subscription is None:
            raise ValueError("Subscription not found")

        now = datetime.now(timezone.utc)
        current_expire = subscription.expires_at

        if current_expire.tzinfo is None:
            current_expire = current_expire.replace(tzinfo=timezone.utc)

        base_date = max(current_expire, now)
        new_expires_at = base_date + timedelta(days=days)
        old_expires_at = current_expire

        try:
            marzban_result = self.marzban.modify_user(
                subscription.marzban_username,
                {
                    "expire": int(new_expires_at.timestamp()),
                },
            )

            subscription.expires_at = new_expires_at
            subscription.status = marzban_result.get(
                "status",
                subscription.status,
            )

            db.commit()
            db.refresh(subscription)
            return {
                "id": subscription.id,
                "username": subscription.marzban_username,
                "expires_at": subscription.expires_at.isoformat(),
                "status": subscription.status,
                "extended_by_days": days,
            }

        except Exception:
            db.rollback()

            try:
                self.marzban.modify_user(
                    subscription.marzban_username,
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
        subscription = (
            db.query(VPNSubscription)
            .filter(VPNSubscription.id == subscription_id)
            .first()
        )

        if subscription is None:
            raise ValueError("Subscription not found")

        username = subscription.marzban_username

        self.marzban.delete_user(username)

        try:
            db.delete(subscription)
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "deleted": True,
            "subscription_id": subscription_id,
            "username": username,
        }


vpn_subscription_service = VPNSubscriptionService()
