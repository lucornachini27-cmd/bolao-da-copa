from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.serializers import match_to_out
from app.core.database import get_db
from app.models.bet import Bet
from app.models.match import Match
from app.models.user import User
from app.schemas.match import MatchOut
from app.schemas.social import MatchBetView
from app.services import bet_service, settings_service
from app.utils.timezone import now_utc

router = APIRouter()


@router.get("", response_model=List[MatchOut])
def list_matches(
    status: Optional[str] = Query(None, description="Filtra por status da API"),
    stage: Optional[str] = Query(None, description="Filtra por fase"),
    defined_only: bool = Query(False, description="Só jogos com as duas seleções definidas"),
    db: Session = Depends(get_db),
):
    query = db.query(Match)
    if status:
        query = query.filter(Match.status == status)
    if stage:
        query = query.filter(Match.stage == stage)
    matches = query.order_by(Match.utc_date.asc()).all()

    lock = settings_service.get_setting_int(db, "bet_lock_minutes", 60)
    out = [match_to_out(m, lock) for m in matches]
    if defined_only:
        out = [m for m in out if m.teams_defined]
    return out


@router.get("/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")
    lock = settings_service.get_setting_int(db, "bet_lock_minutes", 60)
    return match_to_out(match, lock)


@router.get("/{match_id}/bets", response_model=List[MatchBetView])
def match_bets(
    match_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Quem palpitou neste jogo. Os placares só aparecem após o fechamento
    (ou para o admin / o próprio dono do palpite)."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")
    lock = settings_service.get_setting_int(db, "bet_lock_minutes", 60)
    open_now = bet_service.is_open_at(match.status, match.utc_date, now_utc(), lock)

    rows = (
        db.query(Bet, User)
        .join(User, Bet.user_id == User.id)
        .filter(Bet.match_id == match_id, User.is_admin == False)  # noqa: E712
        .order_by(User.name)
        .all()
    )
    result = []
    for bet, participant in rows:
        reveal = viewer.is_admin or bet.user_id == viewer.id or not open_now
        result.append(
            MatchBetView(
                user_id=participant.id,
                user_name=participant.name,
                photo_url=participant.photo_url,
                predicted_home=bet.predicted_home if reveal else None,
                predicted_away=bet.predicted_away if reveal else None,
                points_earned=bet.points_earned if reveal else None,
                revealed=reveal,
            )
        )
    return result
