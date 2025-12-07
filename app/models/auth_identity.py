from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, func
from datetime import datetime
from .base import Base



class AuthIdentity(Base):
    __tablename__ = "auth_identities"

    auth_identities_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_activity.user_activity_id"), nullable=False)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("provider.provider_id"), nullable=False)

    email: Mapped[str] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)

    provider_access_token: Mapped[str] = mapped_column(Text, nullable=True)
    provider_refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    provider_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_activity: Mapped["UserActivity"] = relationship("UserActivity", back_populates="auth_identities")
    provider: Mapped["Provider"] = relationship("Provider", back_populates="auth_identities")
    user_authorizations: Mapped[list["UserAuthorization"]] = relationship("UserAuthorization", back_populates="auth_identity")