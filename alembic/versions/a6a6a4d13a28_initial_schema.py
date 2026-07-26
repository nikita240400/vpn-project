"""initial_schema

Revision ID: a6a6a4d13a28
Revises: 
Create Date: 2026-07-26 05:05:16.104455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6a6a4d13a28'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline existing schema."""
    pass


def downgrade() -> None:
    """Baseline existing schema."""
    pass
