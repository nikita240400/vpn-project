from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class VPNSubscription(Base):
    __tablename__ = "vpn_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    marzban_username: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )

    vpn_uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
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

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    traffic_limit_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship(
        "User",
        back_populates="vpn_subscriptions",
    )