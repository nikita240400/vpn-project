from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class VPNSubscriptionServer(Base):
    __tablename__ = "vpn_subscription_servers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("vpn_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    marzban_username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    vpn_uuid: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    subscription_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    vless_link: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
    )

    subscription = relationship(
    "VPNSubscription",
    back_populates="server_connections",
    )
    server = relationship("Server")