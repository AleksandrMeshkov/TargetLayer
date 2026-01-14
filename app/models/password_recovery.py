from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from typing import Optional
from .base import Base


class PasswordRecovery(Base):
    __tablename__ = "password_recovers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    auth_identities_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("auth_identities.auth_identities_id", ondelete="CASCADE"),
        nullable=False
    )
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    auth_identity: Mapped["AuthIdentity"] = relationship(
        "AuthIdentity",
        backref="password_recoveries"
    )
