from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from .base import Base

class Provider(Base):
    __tablename__ = "provider"

    provider_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    auth_identities: Mapped[list["AuthIdentity"]] = relationship("AuthIdentity", back_populates="provider")