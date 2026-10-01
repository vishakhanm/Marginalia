from unittest.mock import patch
from datetime import datetime, timezone

from app.schemas.auth import UserInfo, TokenResponse


@patch("app.api.auth.auth_service.register_user")
def test_register_endpoint(mock_register, client):
    mock_register.return_value = UserInfo(
        id="u1", email="test@example.com", name="Test", auth_provider="password",
        created_at=datetime.now(timezone.utc),
    )
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@patch("app.api.auth.auth_service.register_user")
def test_register_endpoint_duplicate_email(mock_register, client):
    mock_register.side_effect = ValueError("A user with this email already exists")
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 400


def test_register_endpoint_short_password_rejected(client):
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "short"})
    assert response.status_code == 422  # Pydantic min_length validation


@patch("app.api.auth.auth_service.authenticate_user")
def test_login_endpoint_success(mock_auth, client):
    mock_auth.return_value = TokenResponse(access_token="fake-jwt-token")
    response = client.post(
        "/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"] == "fake-jwt-token"


@patch("app.api.auth.auth_service.authenticate_user")
def test_login_endpoint_invalid_credentials(mock_auth, client):
    mock_auth.side_effect = ValueError("Invalid email or password")
    response = client.post("/auth/login", data={"username": "test@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_me_endpoint_requires_auth(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_endpoint_with_valid_auth(authenticated_client):
    response = authenticated_client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"