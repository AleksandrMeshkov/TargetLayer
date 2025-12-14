from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer
from typing import List, Optional
from .base import Base

class Provider(Base):
    __tablename__ = "providers"
    
    provider_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    auth_type: Mapped[str] = mapped_column(String(20), default="oauth2")
    
    auth_identities: Mapped[List["AuthIdentity"]] = relationship("AuthIdentity", back_populates="provider",cascade="all, delete-orphan")