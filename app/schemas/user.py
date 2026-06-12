from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=4, max_length=128)
    photo_url: Optional[str] = None


class AdminUserCreate(BaseModel):
    """Admin cadastra um participante (senha opcional; padrão 'trocar123')."""
    username: str = Field(min_length=1, max_length=120)
    password: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str            # o "usuário"
    photo_url: Optional[str] = None
    is_admin: bool


class ProfileOut(BaseModel):
    """Perfil: usuário, foto, pontuação total, posição no ranking."""
    id: int
    name: str
    photo_url: Optional[str] = None
    is_admin: bool = False
    total_points: int
    position: Optional[int] = None
    hits: int
