from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class UserActivity(Base):
    __tablename__ = "user_activity"
    
    user_activity_id: Mapped[int] = mapped_column(primary_key=True)
    auth_identities_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_identities.auth_identities_id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    chat_messages_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.chat_messages_id"))
    
    auth_identity: Mapped["AuthIdentity"] = relationship("AuthIdentity", back_populates="user_activities")
    user: Mapped["User"] = relationship("User", back_populates="user_activities")
    chat_message: Mapped["ChatMessage"] = relationship("ChatMessage", back_populates="user_activities")
    goals: Mapped[list["Goal"]] = relationship("Goal", back_populates="user_activity")