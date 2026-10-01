import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user

FAKE_USER = {
    "_id": "user-1",
    "email": "test@example.com",
    "name": "Test User",
    "auth_provider": "password",
    "created_at": datetime.now(timezone.utc),
}


@pytest.fixture
def client():
    """Plain client with no auth override — use for public routes and 401 checks."""
    return TestClient(app)


@pytest.fixture
def authenticated_client():
    """Client with get_current_user overridden to a fixed fake user — use for protected routes."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.pop(get_current_user, None)