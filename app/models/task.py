from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, Text, DateTime
from typing import Optional
from datetime import datetime
from .base import Base

class Task(Base):
    __tablename__ = "tasks"
    
    task_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    roadmaps: Mapped[list["Roadmap"]] = relationship("Roadmap", back_populates="task")