from typing import Optional

from pydantic import BaseModel


class RankingItem(BaseModel):
    position: int
    user_id: int
    name: str
    photo_url: Optional[str] = None
    total_points: int
    hits: int
