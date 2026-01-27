from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Boolean, DateTime
from typing import Optional
from datetime import datetime
from .base import Base

class Roadmap(Base):
    __tablename__ = "roadmaps"
    
    roadmap_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    goals_id: Mapped[int] = mapped_column(Integer, ForeignKey("goals.goals_id", ondelete="CASCADE"), nullable=False, unique=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    goal: Mapped["Goal"] = relationship("Goal", back_populates="roadmap")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="roadmap", cascade="all, delete-orphan")
