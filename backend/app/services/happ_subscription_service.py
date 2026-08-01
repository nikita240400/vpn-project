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


happ_subscription_service = HappSubscriptionService()