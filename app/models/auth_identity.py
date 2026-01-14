from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean
from typing import Optional
from .base import Base

class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    
    auth_identities_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    password: Mapped[Optional[str]] = mapped_column(String(255))
    
    user_activities: Mapped[list["UserActivity"]] = relationship("UserActivity", back_populates="auth_identity")