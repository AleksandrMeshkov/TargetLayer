from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime
from typing import Optional
from datetime import datetime
from .base import Base

class Goal(Base):
    __tablename__ = "goals"
    
    goals_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    roadmaps: Mapped[list["Roadmap"]] = relationship("Roadmap", back_populates="goal")