from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from datetime import datetime
from .base import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    roadmap_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False, index=True)
    goals_id: Mapped[int] = mapped_column(Integer, ForeignKey("goals.goals_id", ondelete="CASCADE"), nullable=False, unique=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    team: Mapped["Team"] = relationship("Team", back_populates="roadmaps")
    goal: Mapped["Goal"] = relationship("Goal", back_populates="roadmap")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="roadmap", cascade="all, delete-orphan")
    access_entries: Mapped[list["RoadmapAccess"]] = relationship(
        "RoadmapAccess", back_populates="roadmap", cascade="all, delete-orphan"
    )
    source_copies: Mapped[list["RoadmapCopy"]] = relationship(
        "RoadmapCopy",
        foreign_keys="RoadmapCopy.original_roadmap_id",
        back_populates="original_roadmap",
        cascade="all, delete-orphan",
    )
    copied_from: Mapped[list["RoadmapCopy"]] = relationship(
        "RoadmapCopy",
        foreign_keys="RoadmapCopy.new_roadmap_id",
        back_populates="new_roadmap",
        cascade="all, delete-orphan",
    )
