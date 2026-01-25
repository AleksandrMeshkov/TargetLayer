from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class UserRoadmap(Base):
    __tablename__ = "user_roadmap"
    
    user_activity_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.roadmap_id"))
    
    user: Mapped["User"] = relationship("User", back_populates="user_roadmaps")
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="user_roadmaps")
