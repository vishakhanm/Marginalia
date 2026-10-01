"""
Auth service — password hashing, registration, login, and the
find-or-create logic used by the Google OAuth callback.
"""

import uuid
from datetime import datetime, timezone

import bcrypt

from app.core.db import get_mongo_db
from app.core.security import create_access_token
from app.schemas.auth import UserInfo, TokenResponse


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def doc_to_user_info(doc: dict) -> UserInfo:
    return UserInfo(
        id=doc["_id"],
        email=doc["email"],
        name=doc.get("name"),
        auth_provider=doc.get("auth_provider", "password"),
        created_at=doc["created_at"],
    )


def register_user(email: str, password: str, name: str | None) -> UserInfo:
    db = get_mongo_db()
    if db.users.find_one({"email": email}):
        raise ValueError("A user with this email already exists")

    user_id = str(uuid.uuid4())
    doc = {
        "_id": user_id,
        "email": email,
        "hashed_password": _hash_password(password),
        "name": name,
        "auth_provider": "password",
        "created_at": datetime.now(timezone.utc),
    }
    db.users.insert_one(doc)
    return doc_to_user_info(doc)


def authenticate_user(email: str, password: str) -> TokenResponse:
    db = get_mongo_db()
    doc = db.users.find_one({"email": email})

    # A user that signed up via Google has no password on file — treat the
    # same as "wrong credentials" rather than leaking which emails exist.
    if not doc or not doc.get("hashed_password"):
        raise ValueError("Invalid email or password")
    if not _verify_password(password, doc["hashed_password"]):
        raise ValueError("Invalid email or password")

    token = create_access_token(subject=doc["_id"])
    return TokenResponse(access_token=token)


def get_or_create_oauth_user(email: str, name: str | None, provider: str) -> UserInfo:
    """
    Used by the Google OAuth callback. If a user with this email already
    exists (e.g. they'd previously registered with a password), we log
    into that same account rather than creating a duplicate.
    """
    db = get_mongo_db()
    doc = db.users.find_one({"email": email})
    if doc:
        return doc_to_user_info(doc)

    user_id = str(uuid.uuid4())
    doc = {
        "_id": user_id,
        "email": email,
        "hashed_password": None,
        "name": name,
        "auth_provider": provider,
        "created_at": datetime.now(timezone.utc),
    }
    db.users.insert_one(doc)
    return doc_to_user_info(doc)