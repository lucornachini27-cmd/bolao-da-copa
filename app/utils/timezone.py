"""Helpers de fuso horário. Regra: guardamos SEMPRE em UTC; convertemos na leitura."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(UTC)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Normaliza para UTC. Datas vindas do SQLite chegam naive: assumimos UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def to_local(dt: datetime | None, tz_name: str | None = None) -> datetime | None:
    """Converte UTC -> fuso local (padrão America/Sao_Paulo, UTC-3)."""
    if dt is None:
        return None
    return ensure_utc(dt).astimezone(ZoneInfo(tz_name or settings.local_timezone))
