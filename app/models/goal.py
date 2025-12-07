from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, func
from datetime import datetime
from .base import Base

class Goal(Base):
    __tablename__ = "goals"

    goals_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_activity.user_activity_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user_activity: Mapped["UserActivity"] = relationship("UserActivity", back_populates="goals")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="goal")
    target_maps: Mapped[list["TargetMap"]] = relationship("TargetMap", back_populates="goal")