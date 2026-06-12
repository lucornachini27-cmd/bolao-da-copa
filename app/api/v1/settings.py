from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.setting import Setting
from app.schemas.setting import SettingOut, SettingUpdate
from app.services import scoring_service, settings_service

# Todas as rotas exigem admin.
router = APIRouter(dependencies=[Depends(require_admin)])

# Alterar estas chaves re-processa a pontuação de todos os jogos finalizados.
POINTS_KEYS = {"points_exact_score", "points_correct_result"}


@router.get("", response_model=List[SettingOut])
def list_settings(db: Session = Depends(get_db)):
    return settings_service.all_settings(db)


@router.put("/{key}", response_model=SettingOut)
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)):
    if db.get(Setting, key) is None:
        raise HTTPException(status_code=404, detail=f"Configuração '{key}' não existe.")
    obj = settings_service.set_setting(db, key, payload.value, payload.description)
    # Mudou a pontuação? reprocessa os jogos já finalizados.
    if key in POINTS_KEYS:
        scoring_service.recalculate_all_finished(db)
    return obj
