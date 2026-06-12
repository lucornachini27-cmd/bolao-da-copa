"""Sincroniza o payload da API para a tabela matches (UPSERT pelo id da API)."""
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import UNDEFINED_TEAM
from app.models.match import Match
from app.schemas.football_data import MatchDTO, MatchesResponseDTO, TeamDTO
from app.services import football_api, scoring_service
from app.utils.timezone import ensure_utc


def _team_name(team: TeamDTO) -> str:
    # shortName é o preferido; cai para name/tla; "A definir" em mata-mata sem times.
    return team.shortName or team.name or team.tla or UNDEFINED_TEAM


def upsert_match(db: Session, dto: MatchDTO) -> Tuple[Match, bool]:
    """Insere ou atualiza uma partida usando o id da API como PK."""
    match = db.get(Match, dto.id)
    is_new = match is None
    if is_new:
        match = Match(id=dto.id)
        db.add(match)

    match.competition = settings.competition_code
    match.stage = dto.stage
    match.group_name = dto.group
    match.utc_date = ensure_utc(dto.utcDate)
    match.status = dto.status
    match.home_team = _team_name(dto.homeTeam)
    match.away_team = _team_name(dto.awayTeam)
    match.home_team_crest = dto.homeTeam.crest
    match.away_team_crest = dto.awayTeam.crest
    match.score_home = dto.score.fullTime.home
    match.score_away = dto.score.fullTime.away
    match.last_updated = ensure_utc(dto.lastUpdated)
    return match, is_new


def sync_matches(db: Session, response: MatchesResponseDTO) -> dict:
    created = 0
    updated = 0
    finished_ids = []
    for dto in response.matches:
        _, is_new = upsert_match(db, dto)
        if is_new:
            created += 1
        else:
            updated += 1
        if dto.status == "FINISHED":
            finished_ids.append(dto.id)
    db.commit()
    return {
        "total": len(response.matches),
        "created": created,
        "updated": updated,
        "finished_ids": finished_ids,
    }


def run_full_sync(db: Session) -> dict:
    """Fluxo completo do botão/cron: busca a API, faz upsert e recalcula pontos."""
    response = football_api.fetch_matches()
    stats = sync_matches(db, response)
    stats["points_recalculated"] = scoring_service.recalculate_all_finished(db)
    return stats
