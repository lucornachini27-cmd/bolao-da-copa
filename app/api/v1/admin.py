"""Ações administrativas (todas exigem is_admin)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.bet import Bet
from app.models.match import Match
from app.models.user import User
from app.schemas.bet import AdminBetCreate, BetOut
from app.schemas.user import AdminUserCreate, UserOut
from app.services import football_api, scoring_service, sync_service

router = APIRouter(dependencies=[Depends(require_admin)])


# ----------------------------- Sincronização -----------------------------
@router.post("/sync")
def trigger_sync(db: Session = Depends(get_db)):
    """Botão 'Atualizar dados': busca a API, faz upsert e recalcula a pontuação."""
    try:
        return sync_service.run_full_sync(db)
    except football_api.FootballApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/recalculate")
def recalculate(db: Session = Depends(get_db)):
    """Reprocessa a pontuação de todos os jogos finalizados."""
    return {"updated": scoring_service.recalculate_all_finished(db)}


@router.post("/resend/{match_id}")
def force_resend(match_id: int, db: Session = Depends(get_db)):
    """Reseta a flag de envio para o scheduler pegar no próximo minuto."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    
    match.preview_sent = 0
    match.result_sent = 0
    db.commit()
    return {"status": "ok", "message": f"Jogo {match_id} resetado."}


# ----------------------------- Participantes -----------------------------
@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.name).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_participant(payload: AdminUserCreate, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if db.query(User).filter(func.lower(User.name) == username.lower()).first():
        raise HTTPException(status_code=400, detail="Usuário já existe.")
    user = User(
        name=username,
        email=f"{username.lower()}@bolao.local",
        password_hash=hash_password(payload.password or "trocar123"),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(user_id: int, db: Session = Depends(get_db)):
    """Exclui um participante e todos os palpites dele (admins não podem ser excluídos)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Não é possível excluir um administrador.")
    db.query(Bet).filter(Bet.user_id == user_id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()


@router.get("/users/{user_id}/bets", response_model=List[BetOut])
def list_user_bets(user_id: int, db: Session = Depends(get_db)):
    return db.query(Bet).filter(Bet.user_id == user_id).all()


# --------------- Lançar/editar palpites em nome do participante ---------------
@router.post("/bets", response_model=BetOut)
def admin_upsert_bet(payload: AdminBetCreate, db: Session = Depends(get_db)):
    """Lança/ajusta o palpite de um participante SEM checar a trava (uso do admin)."""
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    match = db.get(Match, payload.match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    bet = (
        db.query(Bet)
        .filter(Bet.user_id == payload.user_id, Bet.match_id == payload.match_id)
        .first()
    )
    if bet:
        bet.predicted_home = payload.predicted_home
        bet.predicted_away = payload.predicted_away
    else:
        bet = Bet(
            user_id=payload.user_id,
            match_id=payload.match_id,
            predicted_home=payload.predicted_home,
            predicted_away=payload.predicted_away,
        )
        db.add(bet)
    db.commit()
    db.refresh(bet)

    # Se o jogo já finalizou, pontua na hora.
    if match.status == "FINISHED":
        scoring_service.recalculate_match(db, match)
        db.refresh(bet)
    return bet
