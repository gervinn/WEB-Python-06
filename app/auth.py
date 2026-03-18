import hashlib
import os
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from .models import User

SALT_SIZE = 16


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_SIZE).hex()
    password_hash = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(password: str, stored_value: str) -> bool:
    try:
        salt, password_hash = stored_value.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return candidate == password_hash


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login_user(request: Request, user: User) -> None:
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


def logout_user(request: Request) -> None:
    request.session.pop("user", None)


def get_current_user_from_session(request: Request, db: Session) -> Optional[User]:
    user_data = request.session.get("user")
    if not user_data:
        return None
    return db.query(User).filter(User.id == user_data["id"]).first()


def require_login(request: Request, db: Session) -> User:
    user = get_current_user_from_session(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Потрібно увійти в систему")
    return user


def require_admin(request: Request, db: Session) -> User:
    user = require_login(request, db)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ дозволено лише адміністратору")
    return user
