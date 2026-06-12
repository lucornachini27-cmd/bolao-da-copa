from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


def _find_by_username(db: Session, username: str) -> User | None:
    # Login por usuário, sem diferenciar maiúsculas/minúsculas.
    return db.query(User).filter(func.lower(User.name) == username.strip().lower()).first()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if _find_by_username(db, username):
        raise HTTPException(status_code=400, detail="Usuário já existe.")
    user = User(
        name=username,
        email=f"{username.lower()}@bolao.local",  # interno: satisfaz a coluna, nunca exibido
        password_hash=hash_password(payload.password),
        photo_url=payload.photo_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2 usa "username"; aqui é o usuário.
    user = _find_by_username(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
        )
    return Token(access_token=create_access_token(user.id))
