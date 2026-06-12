from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True, index=True)  # = "usuário" (login)
    email = Column(String(255), nullable=True, unique=True, index=True)  # opcional/interno
    password_hash = Column(String(255), nullable=False)  # bcrypt; nunca texto puro
    photo_url = Column(String(255), nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False)  # edita as settings

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bets = relationship("Bet", back_populates="user", cascade="all, delete-orphan")
