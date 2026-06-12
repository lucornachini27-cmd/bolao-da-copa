from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Bet(Base):
    """Palpite de um usuário para uma partida (atrelado ao id da API via FK)."""

    __tablename__ = "bets"
    __table_args__ = (
        # Um único palpite por usuário por partida.
        UniqueConstraint("user_id", "match_id", name="uq_bet_per_user_match"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)

    predicted_home = Column(SmallInteger, nullable=False)
    predicted_away = Column(SmallInteger, nullable=False)

    # Preenchido pelo motor de pontuação quando a partida finaliza.
    points_earned = Column(SmallInteger, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="bets")
    match = relationship("Match", back_populates="bets")
