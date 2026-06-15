"""Schemas das telas sociais: quem palpitou num jogo e perfil de um participante.

Placares ficam ocultos (None) enquanto o jogo aceita palpites, exceto para o
admin ou para o próprio dono do palpite. O campo `revealed` indica isso.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MatchBetView(BaseModel):
    user_id: int
    user_name: str
    photo_url: Optional[str] = None
    predicted_home: Optional[int] = None
    predicted_away: Optional[int] = None
    points_earned: Optional[int] = None
    revealed: bool
    has_bet: bool = True


class ProfileBet(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    local_date: datetime
    status: str
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    predicted_home: Optional[int] = None
    predicted_away: Optional[int] = None
    points_earned: Optional[int] = None
    revealed: bool


class PublicProfile(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None
    total_points: int
    position: Optional[int] = None
    bets: List[ProfileBet]
