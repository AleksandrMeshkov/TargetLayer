"""add team access links

Revision ID: 9c2d71af4b10
Revises: 6f4a1d9b2e11
Create Date: 2026-03-29 21:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c2d71af4b10"
down_revision: Union[str, Sequence[str], None] = "6f4a1d9b2e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column("access_token_type", sa.String(length=32), nullable=False, server_default="invite"),
    )
    op.alter_column("teams", "access_token_type", server_default=None)

    op.create_table(
        "team_access_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("permission", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uses_left", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_team_access_links_team_id"), "team_access_links", ["team_id"], unique=False)
    op.create_index(op.f("ix_team_access_links_token_hash"), "team_access_links", ["token_hash"], unique=False)
    op.create_index(
        op.f("ix_team_access_links_created_by_user_id"),
        "team_access_links",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_team_access_links_created_by_user_id"), table_name="team_access_links")
    op.drop_index(op.f("ix_team_access_links_token_hash"), table_name="team_access_links")
    op.drop_index(op.f("ix_team_access_links_team_id"), table_name="team_access_links")
    op.drop_table("team_access_links")
    op.drop_column("teams", "access_token_type")
