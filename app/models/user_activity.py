from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class UserActivity(Base):
    __tablename__ = "user_activity"
    
    user_activity_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.roadmap_id"))
    
    user: Mapped["User"] = relationship("User", back_populates="user_activities")
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="user_activities")
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="user_activity")