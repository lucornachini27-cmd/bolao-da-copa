"""Inicialização idempotente: cria tabelas, semeia configurações e o admin.

Roda no startup do app (lifespan). Seguro de rodar várias vezes — só cria o
que está faltando. O admin vem das variáveis BOOTSTRAP_ADMIN_USER / _PASSWORD.
"""
from sqlalchemy import func

import app.models  # noqa: F401 — registra os modelos no Base
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User
from app.services import settings_service

_SETTINGS_DEFAULTS = [
    ("points_exact_score", "2", "Bônus por cravar o placar exato (soma com o de vitória)"),
    ("points_correct_result", "1", "Pontos por acertar o vencedor/empate"),
    ("bet_lock_minutes", "60", "Minutos antes do início em que o palpite trava"),
]


def _migrate() -> None:
    """Migrações idempotentes p/ Postgres (em SQLite viram no-op)."""
    from sqlalchemy import text

    for sql in ("ALTER TABLE users ALTER COLUMN photo_url TYPE TEXT",):
        try:
            with engine.begin() as conn:
                conn.execute(text(sql))
        except Exception:
            pass  # SQLite não suporta / coluna já é TEXT


def bootstrap() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate()
    db = SessionLocal()
    try:
        # Configurações padrão (não sobrescreve as existentes).
        for key, value, desc in _SETTINGS_DEFAULTS:
            if settings_service.get_setting(db, key) is None:
                settings_service.set_setting(db, key, value, desc)

        # Admin inicial via variáveis de ambiente (cria só se ainda não existir).
        user = (settings.bootstrap_admin_user or "").strip()
        pw = settings.bootstrap_admin_password or ""
        if user and pw:
            exists = db.query(User).filter(func.lower(User.name) == user.lower()).first()
            if not exists:
                db.add(User(
                    name=user,
                    email=f"{user.lower()}@bolao.local",
                    password_hash=hash_password(pw),
                    is_admin=True,
                ))
                db.commit()
    finally:
        db.close()
