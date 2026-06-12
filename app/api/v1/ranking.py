from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ranking import RankingItem
from app.services import ranking_service

router = APIRouter()


@router.get("", response_model=List[RankingItem])
def leaderboard(db: Session = Depends(get_db)):
    return ranking_service.compute(db)
