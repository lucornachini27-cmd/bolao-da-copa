"""DTOs que espelham o JSON da football-data.org (/competitions/{code}/matches).

Mantemos os nomes em camelCase iguais ao JSON para mapeamento direto e
validação automática do payload (extra="ignore" descarta campos que não usamos).
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TeamDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")
    shortName: Optional[str] = None
    name: Optional[str] = None
    tla: Optional[str] = None
    crest: Optional[str] = None


class FullTimeDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")
    home: Optional[int] = None
    away: Optional[int] = None


class ScoreDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")
    fullTime: FullTimeDTO = FullTimeDTO()


class MatchDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    utcDate: datetime
    status: str
    stage: Optional[str] = None
    group: Optional[str] = None
    lastUpdated: Optional[datetime] = None
    homeTeam: TeamDTO = TeamDTO()
    awayTeam: TeamDTO = TeamDTO()
    score: ScoreDTO = ScoreDTO()


class MatchesResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")
    matches: List[MatchDTO] = []
