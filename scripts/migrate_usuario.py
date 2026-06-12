"""Migração: passa a usar o campo 'usuário' (coluna name) como login único.

Cria o índice único em users(name) no banco existente, sem reconstruir tabela.
    python -m scripts.migrate_usuario
"""
from sqlalchemy import text

import app.models  # noqa: F401
from app.core.database import SessionLocal, engine


def main():
    db = SessionLocal()
    try:
        dupes = db.execute(
            text("SELECT LOWER(name) AS n, COUNT(*) AS c FROM users GROUP BY LOWER(name) HAVING c > 1")
        ).all()
        if dupes:
            print("ATENÇÃO: existem usuários duplicados — resolva antes de criar o índice único:")
            for r in dupes:
                print(f"  - {r.n} (x{r.c})")
            return
        with engine.begin() as conn:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_name ON users(name)"))
        print("OK: índice único em users(name) garantido. Login agora é por usuário.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
