"""add active roadmap to ai conversations

Revision ID: e3f6b5a1c8a2
Revises: 9c2d71af4b10
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e3f6b5a1c8a2"
down_revision: Union[str, Sequence[str], None] = "9c2d71af4b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_conversations",
        sa.Column("active_goal_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ai_conversations",
        sa.Column("active_roadmap_id", sa.Integer(), nullable=True),
    )
    op.create_index(op.f("ix_ai_conversations_active_goal_id"), "ai_conversations", ["active_goal_id"], unique=False)
    op.create_index(op.f("ix_ai_conversations_active_roadmap_id"), "ai_conversations", ["active_roadmap_id"], unique=False)
    op.create_foreign_key(
        "fk_ai_conversations_active_goal_id_goals",
        "ai_conversations",
        "goals",
        ["active_goal_id"],
        ["goals_id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ai_conversations_active_roadmap_id_roadmaps",
        "ai_conversations",
        "roadmaps",
        ["active_roadmap_id"],
        ["roadmap_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_conversations_active_roadmap_id_roadmaps", "ai_conversations", type_="foreignkey")
    op.drop_constraint("fk_ai_conversations_active_goal_id_goals", "ai_conversations", type_="foreignkey")
    op.drop_index(op.f("ix_ai_conversations_active_roadmap_id"), table_name="ai_conversations")
    op.drop_index(op.f("ix_ai_conversations_active_goal_id"), table_name="ai_conversations")
    op.drop_column("ai_conversations", "active_roadmap_id")
    op.drop_column("ai_conversations", "active_goal_id")