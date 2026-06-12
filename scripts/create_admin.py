"""Cria ou promove um administrador (login por usuário).

    python -m scripts.create_admin <usuario> <senha>
"""
import sys

from sqlalchemy import func

import app.models  # noqa: F401 — registra os modelos
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def main():
    if len(sys.argv) < 3:
        print("Uso: python -m scripts.create_admin <usuario> <senha>")
        raise SystemExit(1)
    username, password = sys.argv[1].strip(), sys.argv[2]
    db = SessionLocal()
    try:
        user = db.query(User).filter(func.lower(User.name) == username.lower()).first()
        if user:
            user.is_admin = True
            user.password_hash = hash_password(password)
            print(f"Usuário '{username}' promovido a administrador.")
        else:
            user = User(
                name=username,
                email=f"{username.lower()}@bolao.local",
                password_hash=hash_password(password),
                is_admin=True,
            )
            db.add(user)
            print(f"Administrador '{username}' criado.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
