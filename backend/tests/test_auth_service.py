from unittest.mock import MagicMock, patch
import pytest

from app.services import auth_service


@patch("app.services.auth_service.get_mongo_db")
def test_register_user_success(mock_get_db):
    mock_db = MagicMock()
    mock_db.users.find_one.return_value = None
    mock_get_db.return_value = mock_db

    result = auth_service.register_user("test@example.com", "password123", "Test User")

    assert result.email == "test@example.com"
    assert result.auth_provider == "password"
    mock_db.users.insert_one.assert_called_once()


@patch("app.services.auth_service.get_mongo_db")
def test_register_user_duplicate_email(mock_get_db):
    mock_db = MagicMock()
    mock_db.users.find_one.return_value = {"_id": "existing", "email": "test@example.com"}
    mock_get_db.return_value = mock_db

    with pytest.raises(ValueError, match="already exists"):
        auth_service.register_user("test@example.com", "password123", None)


@patch("app.services.auth_service.get_mongo_db")
def test_authenticate_user_success(mock_get_db):
    hashed = auth_service._hash_password("correct-password")
    mock_db = MagicMock()
    mock_db.users.find_one.return_value = {"_id": "user-1", "hashed_password": hashed}
    mock_get_db.return_value = mock_db

    token = auth_service.authenticate_user("test@example.com", "correct-password")

    assert token.access_token
    assert token.token_type == "bearer"


@patch("app.services.auth_service.get_mongo_db")
def test_authenticate_user_wrong_password(mock_get_db):
    hashed = auth_service._hash_password("correct-password")
    mock_db = MagicMock()
    mock_db.users.find_one.return_value = {"_id": "user-1", "hashed_password": hashed}
    mock_get_db.return_value = mock_db

    with pytest.raises(ValueError, match="Invalid email or password"):
        auth_service.authenticate_user("test@example.com", "wrong-password")


@patch("app.services.auth_service.get_mongo_db")
def test_authenticate_user_oauth_only_account_rejects_password_login(mock_get_db):
    mock_db = MagicMock()
    mock_db.users.find_one.return_value = {"_id": "user-1", "hashed_password": None}
    mock_get_db.return_value = mock_db

    with pytest.raises(ValueError, match="Invalid email or password"):
        auth_service.authenticate_user("test@example.com", "anything")


@patch("app.services.auth_service.get_mongo_db")
def test_get_or_create_oauth_user_creates_new(mock_get_db):
    mock_db = MagicMock()
    mock_db.users.find_one.return_value = None
    mock_get_db.return_value = mock_db

    result = auth_service.get_or_create_oauth_user("new@example.com", "New User", "google")

    assert result.email == "new@example.com"
    assert result.auth_provider == "google"
    mock_db.users.insert_one.assert_called_once()


@patch("app.services.auth_service.get_mongo_db")
def test_get_or_create_oauth_user_finds_existing(mock_get_db):
    from datetime import datetime, timezone

    mock_db = MagicMock()
    mock_db.users.find_one.return_value = {
        "_id": "existing-id",
        "email": "existing@example.com",
        "name": "Existing",
        "auth_provider": "password",
        "created_at": datetime.now(timezone.utc),
    }
    mock_get_db.return_value = mock_db

    result = auth_service.get_or_create_oauth_user("existing@example.com", "Existing", "google")

    assert result.id == "existing-id"
    mock_db.users.insert_one.assert_not_called()