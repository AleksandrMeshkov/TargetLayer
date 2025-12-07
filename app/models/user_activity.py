from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, ForeignKey, func
from datetime import datetime
from .base import Base

class UserActivity(Base):
    __tablename__ = "user_activity"

    user_activity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="user_activities")
    auth_identities: Mapped[list["AuthIdentity"]] = relationship("AuthIdentity", back_populates="user_activity")
    goals: Mapped[list["Goal"]] = relationship("Goal", back_populates="user_activity")
    chats: Mapped[list["Chat"]] = relationship("Chat", secondary="chat_participants", back_populates="user_activities")
    user_authorizations: Mapped[list["UserAuthorization"]] = relationship("UserAuthorization", back_populates="user_activity")