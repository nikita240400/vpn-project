"""add password hash

Revision ID: 3cb582448ef4
Revises: a6a6a4d13a28
Create Date: 2026-07-26 16:36:50.373370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cb582448ef4'
down_revision: Union[str, Sequence[str], None] = 'a6a6a4d13a28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    pass
