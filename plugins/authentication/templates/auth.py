from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt  
from .config import JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db

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

def create_access_token(user: User) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256",
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/authenticate")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
        )

        user_id = payload.get("sub")

        if not user_id or payload.get("type") != "access":
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user
