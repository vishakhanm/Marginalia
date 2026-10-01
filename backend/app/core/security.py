"""
JWT creation/verification and the get_current_user dependency used to
protect routes.

Kept separate from auth_service.py: every protected route needs to
*verify* a token, but only the auth endpoints themselves need
password-hashing logic. This keeps that dependency out of routers
that only care about "is this a valid, logged-in user?".
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings
from app.core.db import get_mongo_db

settings = get_settings()

# tokenUrl tells FastAPI's Swagger UI where to send the login form from the
# "Authorize" button — it doesn't affect how tokens are verified here.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(subject: str) -> str:
    """Issue a JWT whose subject (`sub`) is the user's id."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Return the user id encoded in a valid token, or raise 401."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency: decode the bearer token, look up the user in Mongo,
    and return the raw user document. Raises 401 if the token is missing,
    invalid, expired, or the user no longer exists.
    """
    user_id = decode_access_token(token)
    db = get_mongo_db()
    user = db.users.find_one({"_id": user_id})
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user