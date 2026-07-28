from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class Server(Base):
    __tablename__ = "servers"

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

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    host: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=443,
    )

    marzban_base_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )