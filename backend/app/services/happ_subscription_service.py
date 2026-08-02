from datetime import timezone
from urllib.parse import quote


class HappSubscriptionService:
    """Generates subscription text for Happ."""

    def build_server_links(self, subscription) -> list[str]:
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

        links: list[str] = []

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

        return links

    def build_subscription_text(self, subscription) -> str:
        links = self.build_server_links(subscription)

        if not links:
            return ""

        expires_at = subscription.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc,
            )

        expire_timestamp = int(expires_at.timestamp())

        metadata = [
            "#profile-title: Напальчник VPN",
            "#profile-update-interval: 1",
            (
                "#subscription-userinfo: "
                "upload=0; download=0; total=0; "
                f"expire={expire_timestamp}"
            ),
            "#announce: Натяни по глубже",
        ]

        return "\n".join(metadata + links)


happ_subscription_service = HappSubscriptionService()