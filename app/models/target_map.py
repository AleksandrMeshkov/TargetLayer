from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from typing import Optional, List
from datetime import datetime
from .base import Base

class TargetMap(Base):
    __tablename__ = "target_maps"
    
    target_map_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_activities.user_activity_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow,onupdate=lambda: datetime.utcnow)
    

    user_activity: Mapped["UserActivity"] = relationship("UserActivity", back_populates="target_maps")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="target_map",cascade="all, delete-orphan")