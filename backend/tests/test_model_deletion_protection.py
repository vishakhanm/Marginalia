from unittest.mock import MagicMock, patch
import pytest

from app.services import model_service


def test_default_chat_model_is_protected():
    assert model_service._is_protected(model_service.settings.default_model) is True


def test_default_embedding_model_is_protected():
    assert model_service._is_protected(model_service.settings.default_embedding_model) is True


def test_unrelated_model_is_not_protected():
    assert model_service._is_protected("some-other-model") is False


def test_protected_model_matches_with_tag_suffix():
    """Ollama often returns tagged names like 'llama3.2:latest' — should still match."""
    base = model_service.settings.default_model
    assert model_service._is_protected(f"{base}:latest") is True


@patch("app.services.model_service.get_ollama_client")
def test_delete_protected_model_raises(mock_get_client):
    with pytest.raises(ValueError, match="can't be deleted"):
        model_service.delete_model(model_service.settings.default_model)
    mock_get_client.assert_not_called()  # should never even touch Ollama


@patch("app.services.model_service.get_ollama_client")
def test_delete_unprotected_model_succeeds(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    result = model_service.delete_model("some-other-model")
    assert result.status == "success"