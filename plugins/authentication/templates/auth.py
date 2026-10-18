from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def register_user(db: Session, username: str, password: str) -> User:
    existing_user = db.scalar(
        select(User).where(User.username == username)
    )

    if existing_user:
        raise ValueError("Username already exists")

    user = User(
        username=username,
        password_hash=hash_password(password),
    )

    db.add(user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(
        select(User).where(User.username == username)
    )

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
