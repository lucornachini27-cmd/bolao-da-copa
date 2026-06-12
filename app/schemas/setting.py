from typing import Optional

from pydantic import BaseModel, ConfigDict


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str
    description: Optional[str] = None


class SettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None
