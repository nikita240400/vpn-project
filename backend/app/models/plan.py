from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    days: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    traffic_limit_gb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )