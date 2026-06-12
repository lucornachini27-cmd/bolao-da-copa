from sqlalchemy import BigInteger, Column, DateTime, SmallInteger, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Match(Base):
    """Partida. A PK é o `id` nativo da football-data.org (NÃO auto-incremento)."""

    __tablename__ = "matches"

    # autoincrement=False: gravamos o id que vem da API.
    id = Column(BigInteger, primary_key=True, autoincrement=False)

    competition = Column(String(10), nullable=False, default="WC")
    stage = Column(String(40), nullable=True)        # GROUP_STAGE, ROUND_OF_16...
    group_name = Column(String(20), nullable=True)   # "Group A"...

    utc_date = Column(DateTime(timezone=True), nullable=False, index=True)  # UTC
    status = Column(String(20), nullable=False, index=True)

    home_team = Column(String(80), nullable=False)
    away_team = Column(String(80), nullable=False)
    home_team_crest = Column(String(255), nullable=True)
    away_team_crest = Column(String(255), nullable=True)

    score_home = Column(SmallInteger, nullable=True)  # NULL enquanto não finalizado
    score_away = Column(SmallInteger, nullable=True)

    last_updated = Column(DateTime(timezone=True), nullable=True)  # "lastUpdated" da API
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bets = relationship("Bet", back_populates="match", cascade="all, delete-orphan")
