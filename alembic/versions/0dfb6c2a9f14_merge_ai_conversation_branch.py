"""merge ai conversation branch

Revision ID: 0dfb6c2a9f14
Revises: 9691260d2c50, e3f6b5a1c8a2
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0dfb6c2a9f14"
down_revision: Union[str, Sequence[str], None] = ("9691260d2c50", "e3f6b5a1c8a2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass