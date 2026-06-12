"""Ranking/leaderboard derivado de bets.points_earned (fonte única de verdade)."""
from typing import List

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.bet import Bet
from app.models.user import User


def compute(db: Session) -> List[dict]:
    rows = (
        db.query(
            User.id.label("user_id"),
            User.name.label("name"),
            User.photo_url.label("photo_url"),
            func.coalesce(func.sum(Bet.points_earned), 0).label("total"),
            func.coalesce(func.sum(case((Bet.points_earned > 0, 1), else_=0)), 0).label("hits"),
        )
        .outerjoin(Bet, Bet.user_id == User.id)
        .filter(User.is_admin == False)  # noqa: E712 — admin não entra no ranking
        .group_by(User.id, User.name, User.photo_url)
        .order_by(func.coalesce(func.sum(Bet.points_earned), 0).desc(), User.name.asc())
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
            }
        )
    return ranking
