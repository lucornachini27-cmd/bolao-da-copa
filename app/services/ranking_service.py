"""Ranking/leaderboard derivado de bets.points_earned (fonte única de verdade)."""
from typing import List

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.bet import Bet
from app.models.match import Match
from app.models.user import User


def compute(db: Session) -> List[dict]:
    # "Cravadas": palpite idêntico ao placar final (o que rende o bônus de placar exato).
    exact_case = case(
        (
            (Match.status == "FINISHED")
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
    return ranking
