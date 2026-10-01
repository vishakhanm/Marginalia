from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from app.core.security import create_access_token, decode_access_token
from app.core.config import get_settings

settings = get_settings()


def test_create_and_decode_token_roundtrip():
    token = create_access_token(subject="user-123")
    user_id = decode_access_token(token)
    assert user_id == "user-123"


def test_decode_garbage_token_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-real-token")
    assert exc_info.value.status_code == 401


def test_decode_expired_token_raises_401():
    expired_payload = {
        "sub": "user-123",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(
        expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)
    assert exc_info.value.status_code == 401


def test_decode_token_signed_with_wrong_key_raises_401():
    bad_token = jwt.encode({"sub": "user-123"}, "some-other-secret", algorithm=settings.jwt_algorithm)
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(bad_token)
    assert exc_info.value.status_code == 401