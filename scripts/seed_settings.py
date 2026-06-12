"""Popula as configurações padrão do motor de pontuação.
    python -m scripts.seed_settings
"""
import app.models  # noqa: F401
from app.core.database import SessionLocal
from app.services import settings_service

DEFAULTS = [
    ("points_exact_score", "2", "Bônus por cravar o placar exato (soma com o de vitória)"),
    ("points_correct_result", "1", "Pontos por acertar o vencedor/empate"),
    ("bet_lock_minutes", "60", "Minutos antes do início em que o palpite trava"),
]


def main():
    db = SessionLocal()
    try:
        for key, value, description in DEFAULTS:
            if settings_service.get_setting(db, key) is None:
                settings_service.set_setting(db, key, value, description)
                print(f"  + {key} = {value}")
            else:
                print(f"  = {key} já existe ({settings_service.get_setting(db, key)})")
    finally:
        db.close()
    print("Seed de configurações concluído.")


if __name__ == "__main__":
    main()
