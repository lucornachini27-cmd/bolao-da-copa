from typing import Optional

from pydantic import BaseModel


class RankingItem(BaseModel):
    position: int
    user_id: int
    name: str
    photo_url: Optional[str] = None
    total_points: int
    hits: int
    exact_hits: int = 0  # nº de placares cravados (bônus de placar exato)
    delta: int = 0       # variação de posição no dia (+ subiu, - desceu)
