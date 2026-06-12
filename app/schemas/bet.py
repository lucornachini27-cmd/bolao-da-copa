from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BetCreate(BaseModel):
    match_id: int
    predicted_home: int = Field(ge=0, le=99)
    predicted_away: int = Field(ge=0, le=99)


class AdminBetCreate(BaseModel):
    """Admin lança/edita o palpite de um participante (ignora a trava)."""
    user_id: int
    match_id: int
    predicted_home: int = Field(ge=0, le=99)
    predicted_away: int = Field(ge=0, le=99)


class BetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    match_id: int
    predicted_home: int
    predicted_away: int
    points_earned: int


class BetHistoryItem(BaseModel):
    """Palpite lado a lado com o resultado real da partida."""
    match_id: int
    home_team: str
    away_team: str
    utc_date: datetime
    local_date: datetime
    status: str
    predicted_home: int
    predicted_away: int
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    points_earned: int
    is_open: bool
