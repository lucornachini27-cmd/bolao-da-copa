from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.serializers import bet_to_history
from app.core.database import get_db
from app.models.bet import Bet
from app.models.match import Match
from app.models.user import User
from app.schemas.bet import BetCreate, BetHistoryItem, BetOut
from app.services import bet_service, settings_service

router = APIRouter()


@router.post("", response_model=BetOut)
def upsert_bet(
    payload: BetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria ou edita o palpite. A regra de bloqueio é validada no backend."""
    match = db.get(Match, payload.match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    # Regra de bloqueio: 1h (configurável) antes do utcDate.
    try:
        bet_service.assert_bet_open(db, match)
    except bet_service.BetLockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    bet = (
        db.query(Bet)
        .filter(Bet.user_id == user.id, Bet.match_id == match.id)
        .first()
    )
    if bet:
        bet.predicted_home = payload.predicted_home
        bet.predicted_away = payload.predicted_away
    else:
        bet = Bet(
            user_id=user.id,
            match_id=match.id,
            predicted_home=payload.predicted_home,
            predicted_away=payload.predicted_away,
        )
        db.add(bet)
    db.commit()
    db.refresh(bet)
    return bet


@router.get("/me", response_model=List[BetHistoryItem])
def my_bets(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Histórico de palpites do usuário lado a lado com o resultado real."""
    bets = (
        db.query(Bet)
        .join(Match, Bet.match_id == Match.id)
        .filter(Bet.user_id == user.id)
        .order_by(Match.utc_date.asc())
        .all()
    )
    lock = settings_service.get_setting_int(db, "bet_lock_minutes", 60)
    return [bet_to_history(b.match, b, lock) for b in bets]
