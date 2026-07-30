"""add server id to vpn subscriptions

Revision ID: 9a34eb5fe0fd
Revises: 9f4626e21e62
Create Date: 2026-07-28 05:01:28.667575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a34eb5fe0fd'
down_revision: Union[str, Sequence[str], None] = '9f4626e21e62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "vpn_subscriptions",
        sa.Column(
            "server_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE vpn_subscriptions
        SET server_id = 1
        WHERE server_id IS NULL
        """
    )

    op.alter_column(
        "vpn_subscriptions",
        "server_id",
        nullable=False,
    )

    op.create_index(
        op.f("ix_vpn_subscriptions_server_id"),
        "vpn_subscriptions",
        ["server_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_vpn_subscriptions_server_id",
        "vpn_subscriptions",
        "servers",
        ["server_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_vpn_subscriptions_server_id",
        "vpn_subscriptions",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_vpn_subscriptions_server_id"),
        table_name="vpn_subscriptions",
    )

    op.drop_column(
        "vpn_subscriptions",
        "server_id",
    )
