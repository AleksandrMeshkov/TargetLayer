from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, Text, DateTime
from typing import Optional
from datetime import datetime
from .base import Base

class Goal(Base):
    __tablename__ = "goals"
    
    goals_id: Mapped[int] = mapped_column(primary_key=True)
    user_activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_activity.user_activity_id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    user_activity: Mapped["UserActivity"] = relationship("UserActivity", back_populates="goals")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="goal")