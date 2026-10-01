from unittest.mock import MagicMock, patch
from ollama import ResponseError

from app.services import model_service


@patch("app.services.model_service.get_ollama_client")
def test_list_models(mock_get_client):
    mock_client = MagicMock()
    mock_client.list.return_value = {
        "models": [
            {
                "model": "llama3.2:latest",
                "size": 2000000000,
                "details": {"parameter_size": "3B", "quantization_level": "Q4_0"},
                "modified_at": "2025-01-01T00:00:00Z",
            }
        ]
    }
    mock_get_client.return_value = mock_client

    result = model_service.list_models()

    assert result.count == 1
    assert result.models[0].name == "llama3.2:latest"
    assert result.models[0].parameter_size == "3B"


@patch("app.services.model_service.get_ollama_client")
def test_pull_model_success(mock_get_client):
    mock_client = MagicMock()
    mock_client.pull.return_value = None
    mock_get_client.return_value = mock_client

    result = model_service.pull_model("llama3.2")

    assert result.status == "success"
    assert result.name == "llama3.2"
    mock_client.pull.assert_called_once_with(model="llama3.2")


@patch("app.services.model_service.get_ollama_client")
def test_pull_model_failure(mock_get_client):
    mock_client = MagicMock()
    mock_client.pull.side_effect = ResponseError("model not found")
    mock_get_client.return_value = mock_client

    result = model_service.pull_model("nonexistent-model")

    assert result.status == "error"
    assert result.detail is not None


@patch("app.services.model_service.get_ollama_client")
def test_delete_model_success(mock_get_client):
    mock_client = MagicMock()
    mock_client.delete.return_value = None
    mock_get_client.return_value = mock_client

    result = model_service.delete_model("mistral")

    assert result.status == "success"
    mock_client.delete.assert_called_once_with(model="mistral")