from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat
    from .roadmap import Roadmap
    from .team_access_link import TeamAccessLink
    from .team_member import TeamMember


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    access_token_type: Mapped[str] = mapped_column(String(32), nullable=False, default="invite")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    roadmaps: Mapped[list["Roadmap"]] = relationship(
        "Roadmap", back_populates="team", cascade="all, delete-orphan"
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat", back_populates="team", cascade="all, delete-orphan"
    )
    access_links: Mapped[list["TeamAccessLink"]] = relationship(
        "TeamAccessLink", back_populates="team", cascade="all, delete-orphan"
    )
