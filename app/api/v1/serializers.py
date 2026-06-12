"""Conversão ORM -> schemas de saída (hora local, contador e flag de bloqueio).

O `lock_minutes` é lido UMA vez por request e repassado, evitando uma consulta
à tabela settings por partida.
"""
from datetime import datetime
from typing import Optional

from app.models.bet import Bet
from app.models.match import Match
from app.schemas.bet import BetHistoryItem
from app.schemas.match import MatchOut
from app.services import bet_service
from app.utils.timezone import now_utc, to_local


def match_to_out(match: Match, lock_minutes: int, now: Optional[datetime] = None) -> MatchOut:
    now = now or now_utc()
    defined = bet_service.teams_defined(match.home_team, match.away_team)
    is_open = defined and bet_service.is_open_at(
        match.status, match.utc_date, now, lock_minutes
    )
    return MatchOut(
        id=match.id,
        competition=match.competition,
        stage=match.stage,
        group_name=match.group_name,
        utc_date=match.utc_date,
        local_date=to_local(match.utc_date),
        closes_at=bet_service.closes_at(match.utc_date, lock_minutes),
        status=match.status,
        home_team=match.home_team,
        away_team=match.away_team,
        home_team_crest=match.home_team_crest,
        away_team_crest=match.away_team_crest,
        score_home=match.score_home,
        score_away=match.score_away,
        teams_defined=defined,
        is_open=is_open,
    )


def bet_to_history(
    match: Match, bet: Bet, lock_minutes: int, now: Optional[datetime] = None
) -> BetHistoryItem:
    now = now or now_utc()
    is_open = bet_service.teams_defined(match.home_team, match.away_team) and bet_service.is_open_at(
        match.status, match.utc_date, now, lock_minutes
    )
    return BetHistoryItem(
        match_id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        utc_date=match.utc_date,
        local_date=to_local(match.utc_date),
        status=match.status,
        predicted_home=bet.predicted_home,
        predicted_away=bet.predicted_away,
        score_home=match.score_home,
        score_away=match.score_away,
        points_earned=bet.points_earned,
        is_open=is_open,
    )
