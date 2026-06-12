from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MatchOut(BaseModel):
    id: int
    competition: str
    stage: Optional[str] = None
    group_name: Optional[str] = None
    utc_date: datetime           # UTC (padrão)
    local_date: datetime         # America/Sao_Paulo
    closes_at: datetime          # quando o palpite fecha (UTC) — base do contador
    status: str
    home_team: str
    away_team: str
    home_team_crest: Optional[str] = None
    away_team_crest: Optional[str] = None
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    teams_defined: bool          # False quando ainda é "A definir"
    is_open: bool                # aceita palpite agora?
