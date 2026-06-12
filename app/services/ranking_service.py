"""Ranking/leaderboard derivado de bets.points_earned (fonte única de verdade)."""
import json
from typing import List

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.bet import Bet
from app.models.match import Match
from app.models.user import User
from app.services import settings_service
from app.utils.timezone import now_utc, to_local


def compute(db: Session) -> List[dict]:
    # "Cravadas": palpite idêntico ao placar (o que rende o bônus de placar exato).
    exact_case = case(
        (
            (Match.status.in_(["FINISHED", "IN_PLAY", "PAUSED", "AWARDED"]))
            & (Bet.predicted_home == Match.score_home)
            & (Bet.predicted_away == Match.score_away),
            1,
        ),
        else_=0,
    )
    rows = (
        db.query(
            User.id.label("user_id"),
            User.name.label("name"),
            User.photo_url.label("photo_url"),
            func.coalesce(func.sum(Bet.points_earned), 0).label("total"),
            func.coalesce(func.sum(case((Bet.points_earned > 0, 1), else_=0)), 0).label("hits"),
            func.coalesce(func.sum(exact_case), 0).label("exact_hits"),
        )
        .outerjoin(Bet, Bet.user_id == User.id)
        .outerjoin(Match, Match.id == Bet.match_id)
        .filter(User.is_admin == False)  # noqa: E712 — admin não entra no ranking
        .group_by(User.id, User.name, User.photo_url)
        .order_by(
            func.coalesce(func.sum(Bet.points_earned), 0).desc(),       # 1º: pontos
            func.coalesce(func.sum(exact_case), 0).desc(),              # desempate: cravadas
            User.name.asc(),
        )
        .all()
    )

    ranking = []
    for position, row in enumerate(rows, start=1):
        ranking.append(
            {
                "position": position,
                "user_id": row.user_id,
                "name": row.name,
                "photo_url": row.photo_url,
                "total_points": int(row.total or 0),
                "hits": int(row.hits or 0),
                "exact_hits": int(row.exact_hits or 0),
            }
        )
    _apply_daily_movement(db, ranking)
    return ranking


def _apply_daily_movement(db: Session, ranking: List[dict]) -> None:
    """Variação de posição do dia (seta ↑/↓), guardada na tabela settings.

    Tira um 'retrato' das posições 1x por dia (horário de Brasília). Durante o
    dia, delta = posição do retrato − posição atual (positivo = subiu).
    """
    today = to_local(now_utc()).date().isoformat()
    snap_date = settings_service.get_setting(db, "ranking_snap_date")
    raw = settings_service.get_setting(db, "ranking_prev_pos")
    prev = {}
    if raw:
        try:
            prev = json.loads(raw)
        except (ValueError, TypeError):
            prev = {}

    if snap_date != today:
        snapshot = {str(e["user_id"]): e["position"] for e in ranking}
        settings_service.set_setting(db, "ranking_prev_pos", json.dumps(snapshot))
        settings_service.set_setting(db, "ranking_snap_date", today)
        for e in ranking:
            e["delta"] = 0
    else:
        for e in ranking:
            p = prev.get(str(e["user_id"]))
            e["delta"] = (p - e["position"]) if isinstance(p, int) else 0
