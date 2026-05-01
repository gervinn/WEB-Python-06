import hashlib
import hmac
import os
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, Request, status
from pymongo.database import Database

PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{salt.hex()}${password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
    except ValueError:
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(actual_hash, expected_hash)


def get_current_user(request: Request, db: Database) -> Optional[dict]:
    user_id = request.session.get("user_id")
    if not user_id or not ObjectId.is_valid(user_id):
        return None
    return db.users.find_one({"_id": ObjectId(user_id)})


def require_api_user(request: Request, db: Database) -> dict:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Потрібно увійти в обліковий запис",
        )
    return user


def require_api_admin(request: Request, db: Database) -> dict:
    user = require_api_user(request, db)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ дозволено тільки адміністратору",
        )
    return user
