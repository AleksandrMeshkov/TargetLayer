from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class UserAuthorization(Base):
    __tablename__ = "user_authorization"

    user_authorization_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auth_identities_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_identities.auth_identities_id"), nullable=False)
    user_activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_activity.user_activity_id"), nullable=False)

    auth_identity: Mapped["AuthIdentity"] = relationship("AuthIdentity", back_populates="user_authorizations")
    user_activity: Mapped["UserActivity"] = relationship("UserActivity", back_populates="user_authorizations")