from datetime import datetime, timedelta, timezone

from backend.app.services.marzban import marzban_client


class VPNSubscriptionService:
    def __init__(self):
        self.marzban = marzban_client

    def create_subscription(
        self,
        username: str,
        days: int,
        traffic_gb: int | None,
        note: str | None,
    ):
        expire = int(
            (
                datetime.now(timezone.utc)
                + timedelta(days=days)
            ).timestamp()
        )

        payload = {
            "username": username,
            "status": "active",
            "expire": expire,
            "data_limit": (
                traffic_gb * 1024 * 1024 * 1024
                if traffic_gb
                else 0
            ),
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

        return self.marzban.create_user(payload)


vpn_subscription_service = VPNSubscriptionService()