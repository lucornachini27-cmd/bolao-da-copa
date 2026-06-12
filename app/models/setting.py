from sqlalchemy import Column, DateTime, String, func

from app.core.database import Base


class Setting(Base):
    """Configuração chave-valor. Motor de pontuação NÃO chumbado no código."""

    __tablename__ = "settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
