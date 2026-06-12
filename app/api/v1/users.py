from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.bet import Bet
from app.models.match import Match
from app.models.user import User
from app.schemas.social import ProfileBet, PublicProfile
from app.schemas.user import ProfileOut, UserOut, UserUpdate
from app.services import bet_service, ranking_service, settings_service
from app.utils.timezone import now_utc, to_local

router = APIRouter()


@router.get("/me", response_model=ProfileOut)
def my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Perfil: foto, pontuação total e posição no ranking."""
    ranking = ranking_service.compute(db)
    entry = next((r for r in ranking if r["user_id"] == user.id), None)
    return ProfileOut(
        id=user.id,
        name=user.name,
        photo_url=user.photo_url,
        is_admin=user.is_admin,
        total_points=entry["total_points"] if entry else 0,
        position=entry["position"] if entry else None,
        hits=entry["hits"] if entry else 0,
    )


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Atualiza o próprio nome (usuário) e/ou a foto de perfil."""
    if payload.name is not None:
        new_name = payload.name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="O nome não pode ficar vazio.")
        clash = (
            db.query(User)
            .filter(func.lower(User.name) == new_name.lower(), User.id != user.id)
            .first()
        )
        if clash:
            raise HTTPException(status_code=400, detail="Esse usuário já está em uso.")
        user.name = new_name
    if payload.photo_url is not None:
        photo = payload.photo_url or None
        if photo and len(photo) > 300_000:
            raise HTTPException(status_code=400, detail="Imagem muito grande (tente outra).")
        user.photo_url = photo
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/profile", response_model=PublicProfile)
def user_profile(
    user_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Perfil de um participante: pontos, posição e histórico de palpites.

    Palpites de jogos ainda abertos ficam ocultos, exceto para o admin
    ou para o próprio dono do perfil."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    ranking = ranking_service.compute(db)
    entry = next((r for r in ranking if r["user_id"] == user_id), None)
    lock = settings_service.get_setting_int(db, "bet_lock_minutes", 60)
    now = now_utc()

    bets = (
        db.query(Bet)
        .join(Match, Bet.match_id == Match.id)
        .filter(Bet.user_id == user_id)
        .order_by(Match.utc_date.asc())
        .all()
    )
    items: List[ProfileBet] = []
    for b in bets:
        m = b.match
        reveal = (
            viewer.is_admin
            or viewer.id == user_id
            or not bet_service.is_open_at(m.status, m.utc_date, now, lock)
        )
        items.append(
            ProfileBet(
                match_id=m.id,
                home_team=m.home_team,
                away_team=m.away_team,
                local_date=to_local(m.utc_date),
                status=m.status,
                score_home=m.score_home,
                score_away=m.score_away,
                predicted_home=b.predicted_home if reveal else None,
                predicted_away=b.predicted_away if reveal else None,
                points_earned=b.points_earned if reveal else None,
                revealed=reveal,
            )
        )
    return PublicProfile(
        id=target.id,
        name=target.name,
        photo_url=target.photo_url,
        total_points=entry["total_points"] if entry else 0,
        position=entry["position"] if entry else None,
        bets=items,
    )
