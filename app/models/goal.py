from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from typing import Optional
from datetime import datetime
from .base import Base

class Goal(Base):
    __tablename__ = "goals"
    
    goals_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="goals")
    roadmap: Mapped[Optional["Roadmap"]] = relationship("Roadmap", back_populates="goal", uselist=False, cascade="all, delete-orphan")