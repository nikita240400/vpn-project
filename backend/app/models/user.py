from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    vpn_subscriptions = relationship(
        "VPNSubscription",
         back_populates="user",
        cascade="all, delete-orphan",
)
