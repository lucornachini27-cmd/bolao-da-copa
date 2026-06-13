"""Fonte de placares: ESPN scoreboard (público, tempo real, sem chave).

Normaliza o payload da ESPN para o nosso `MatchDTO` interno. Os estados da ESPN
(pre/in/post) viram o vocabulário do sistema (TIMED/IN_PLAY/FINISHED), então a
trava de palpite e a pontuação continuam funcionando sem alteração.

Endpoint: GET {espn_scoreboard_url}?dates=YYYYMMDD-YYYYMMDD  (a janela inteira
da Copa vem numa requisição só).
"""
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.constants import UNDEFINED_TEAM
from app.core.team_names import to_pt

# Estado da ESPN -> status interno do bolão.
_STATE_MAP = {"pre": "TIMED", "in": "IN_PLAY", "post": "FINISHED"}


class FootballApiError(Exception):
    """Erro ao consumir a API externa (rede ou payload)."""


class MatchDTO(BaseModel):
    """Partida já normalizada (independente da fonte de dados)."""
    id: int
    utc_date: datetime
    status: str
    home_team: str
    away_team: str
    home_team_crest: Optional[str] = None
    away_team_crest: Optional[str] = None
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    stage: Optional[str] = None
    group_name: Optional[str] = None


def _to_utc(value: str) -> datetime:
    """ESPN manda algo como '2026-06-12T19:00Z'."""
    dt = datetime.fromisoformat(value.strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _team_name(team: Optional[dict]) -> str:
    team = team or {}
    name = (team.get("shortDisplayName") or team.get("displayName") or "").strip()
    # Seleções reais sempre têm escudo/bandeira; slots de mata-mata indefinidos
    # (ex.: "RD16 W7", sem logo) viram "A definir" e ficam ocultos até saírem os times.
    if not name or not team.get("logo") or name.upper() in {"TBD", "TBA"}:
        return UNDEFINED_TEAM
    return to_pt(name)


def _score(raw, state: str) -> Optional[int]:
    # Antes do jogo o placar não tem significado; só conta de 'in'/'post' em diante.
    if state == "pre" or raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _parse_event(event: dict) -> Optional[MatchDTO]:
    competitions = event.get("competitions") or []
    if not competitions:
        return None
    competitors = competitions[0].get("competitors") or []
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None

    state = ((event.get("status") or {}).get("type") or {}).get("state", "pre")
    home_team = home.get("team") or {}
    away_team = away.get("team") or {}
    return MatchDTO(
        id=int(event["id"]),
        utc_date=_to_utc(event["date"]),
        status=_STATE_MAP.get(state, "TIMED"),
        home_team=_team_name(home_team),
        away_team=_team_name(away_team),
        home_team_crest=home_team.get("logo"),
        away_team_crest=away_team.get("logo"),
        score_home=_score(home.get("score"), state),
        score_away=_score(away.get("score"), state),
    )


def fetch_matches() -> List[MatchDTO]:
    """Busca o scoreboard da Copa na ESPN (janela inteira) e devolve normalizado."""
    try:
        resp = httpx.get(
            settings.espn_scoreboard_url,
            params={"dates": settings.espn_dates},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=25.0,
        )
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPError as exc:
        raise FootballApiError(f"Erro ao consumir a ESPN: {exc}") from exc

    matches: List[MatchDTO] = []
    for event in payload.get("events", []):
        try:
            dto = _parse_event(event)
        except Exception:
            dto = None  # um evento malformado não derruba a sincronização inteira
        if dto:
            matches.append(dto)

    if not matches:
        raise FootballApiError("ESPN não retornou jogos para a janela configurada.")
    return matches
