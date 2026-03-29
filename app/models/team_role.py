from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .team_member import TeamMember


class TeamRole(Base):
    __tablename__ = "team_role"

    team_role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    members: Mapped[list["TeamMember"]] = relationship("TeamMember", back_populates="team_role")
