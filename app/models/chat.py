from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ForeignKey
from typing import Optional
from datetime import datetime
from .base import Base

class Chat(Base):
    __tablename__ = "chats"
    
    chat_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), default="team", nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    team: Mapped["Team"] = relationship("Team", back_populates="chats")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    participants: Mapped[list["ChatParticipant"]] = relationship(
        "ChatParticipant", back_populates="chat", cascade="all, delete-orphan"
    )