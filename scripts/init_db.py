"""Cria todas as tabelas — atalho de MVP para SQLite (sem Alembic).

Produção/PostgreSQL: prefira `alembic upgrade head`.
    python -m scripts.init_db
"""
import app.models  # noqa: F401  (registra os models no metadata)
from app.core.database import Base, engine


def main():
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas/atualizadas com sucesso.")


if __name__ == "__main__":
    main()
