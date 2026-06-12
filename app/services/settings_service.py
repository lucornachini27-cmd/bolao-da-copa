"""Leitura/escrita das configurações (tabela settings)."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.setting import Setting


def get_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    obj = db.get(Setting, key)
    return obj.value if obj else default


def get_setting_int(db: Session, key: str, default: int = 0) -> int:
    raw = get_setting(db, key, None)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def set_setting(
    db: Session, key: str, value, description: Optional[str] = None
) -> Setting:
    obj = db.get(Setting, key)
    if obj:
        obj.value = str(value)
        if description is not None:
            obj.description = description
    else:
        obj = Setting(key=key, value=str(value), description=description)
        db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def all_settings(db: Session) -> List[Setting]:
    return db.query(Setting).order_by(Setting.key).all()
