"""Sincroniza as partidas normalizadas no banco (UPSERT pelo id da fonte)."""
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.match import Match
from app.services import football_api, scoring_service
from app.services.football_api import MatchDTO
from app.utils.timezone import now_utc


def sync_matches(db: Session, matches: Iterable[MatchDTO]) -> dict:
    """Insere/atualiza cada partida. O id da fonte é a PK (cruza com os palpites)."""
    matches = list(matches)
    created = 0
    updated = 0
    finished_ids = []
    for m in matches:
        row = db.get(Match, m.id)
        if row is None:
            row = Match(id=m.id)
            db.add(row)
            created += 1
        else:
            updated += 1
        row.competition = settings.competition_code
        row.utc_date = m.utc_date
        row.status = m.status
        row.home_team = m.home_team
        row.away_team = m.away_team
        row.home_team_crest = m.home_team_crest
        row.away_team_crest = m.away_team_crest
        row.score_home = m.score_home
        row.score_away = m.score_away
        row.stage = m.stage
        row.group_name = m.group_name
        row.last_updated = now_utc()
        if m.status == "FINISHED":
            finished_ids.append(m.id)
    db.commit()
    return {
        "total": len(matches),
        "created": created,
        "updated": updated,
        "finished_ids": finished_ids,
    }


def run_full_sync(db: Session) -> dict:
    """Fluxo completo do botão/cron: busca a ESPN, faz upsert e recalcula pontos."""
    matches = football_api.fetch_matches()
    stats = sync_matches(db, matches)
    stats["points_recalculated"] = scoring_service.recalculate_all_finished(db)
    return stats
