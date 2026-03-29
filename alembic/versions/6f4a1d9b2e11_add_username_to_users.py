"""add username to users

Revision ID: 6f4a1d9b2e11
Revises: 3a537847133f
Create Date: 2026-03-29 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f4a1d9b2e11"
down_revision: Union[str, Sequence[str], None] = "3a537847133f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=100), nullable=True))

    # Backfill existing rows with deterministic unique values.
    op.execute(
        """
        UPDATE users
        SET username = split_part(email, '@', 1) || '_' || user_id
        WHERE username IS NULL
        """
    )

    op.alter_column("users", "username", nullable=False)
    op.create_unique_constraint("uq_users_username", "users", ["username"])


def downgrade() -> None:
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "username")
