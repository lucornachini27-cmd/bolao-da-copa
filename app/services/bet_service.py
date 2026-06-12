"""Regra de bloqueio de palpite.

Um palpite só está ABERTO quando, simultaneamente:
  1. as duas seleções estão definidas (não "A definir");
  2. o status permite (jogo ainda não começou);
  3. faltam mais de N minutos para o início (N vem da tabela settings).
Tudo validado no backend.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.constants import UNDEFINED_TEAM
from app.models.match import Match
from app.services import settings_service
from app.utils.timezone import ensure_utc, now_utc

# Só aceita palpite enquanto a partida não começou.
OPEN_STATUSES = {"SCHEDULED", "TIMED"}


class BetLockedError(Exception):
    """Palpite recusado: janela de aposta fechada."""


def closes_at(utc_date: datetime, lock_minutes: int) -> datetime:
    """Instante (UTC) em que o palpite fecha."""
    return ensure_utc(utc_date) - timedelta(minutes=lock_minutes)


def teams_defined(home_team: str, away_team: str) -> bool:
    """Só há palpite quando as duas seleções estão definidas."""
    return home_team != UNDEFINED_TEAM and away_team != UNDEFINED_TEAM


def is_open_at(status: str, utc_date: datetime, now: datetime, lock_minutes: int) -> bool:
    """Janela de TEMPO + status (função pura, testável)."""
    if status not in OPEN_STATUSES:
        return False
    return now < closes_at(utc_date, lock_minutes)


def _lock_minutes(db: Session) -> int:
    return settings_service.get_setting_int(db, "bet_lock_minutes", 60)


def is_bet_open(db: Session, match: Match) -> bool:
    return teams_defined(match.home_team, match.away_team) and is_open_at(
        match.status, match.utc_date, now_utc(), _lock_minutes(db)
    )


def assert_bet_open(db: Session, match: Match) -> None:
    """Levanta BetLockedError se a aposta não for permitida."""
    if not teams_defined(match.home_team, match.away_team):
        raise BetLockedError("As seleções deste jogo ainda não estão definidas.")
    lock_minutes = _lock_minutes(db)
    if match.status not in OPEN_STATUSES:
        raise BetLockedError("A partida já começou ou foi finalizada.")
    if not is_open_at(match.status, match.utc_date, now_utc(), lock_minutes):
        raise BetLockedError(
            f"Palpites bloqueados {lock_minutes} minutos antes do início da partida."
        )
