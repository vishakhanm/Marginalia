from unittest.mock import MagicMock, patch
import pytest

from app.services import endpoint_service
from app.schemas.hyperparameters import HyperparameterSettings
from app.schemas.rag import ChatResponse


@patch("app.services.endpoint_service.get_mongo_db")
def test_create_endpoint(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    hp = HyperparameterSettings(temperature=0.2, top_k=3)
    result = endpoint_service.create_endpoint("legal-qa", "kb-1", hp)

    assert result.name == "legal-qa"
    assert result.kb_id == "kb-1"
    assert result.hyperparameters.temperature == 0.2
    assert result.call_count == 0
    mock_db.endpoints.insert_one.assert_called_once()


@patch("app.services.endpoint_service.get_mongo_db")
def test_get_endpoint_not_found(mock_get_db):
    mock_db = MagicMock()
    mock_db.endpoints.find_one.return_value = None
    mock_get_db.return_value = mock_db

    assert endpoint_service.get_endpoint("missing-id") is None


@patch("app.services.rag_service.generate_answer")
@patch("app.services.endpoint_service.get_mongo_db")
def test_invoke_endpoint_success(mock_get_db, mock_generate):
    mock_db = MagicMock()
    mock_db.endpoints.find_one.return_value = {
        "_id": "ep-1",
        "name": "legal-qa",
        "kb_id": "kb-1",
        "hyperparameters": {"temperature": 0.2},
        "created_at": "2025-01-01T00:00:00Z",
        "call_count": 2,
        "last_called_at": None,
    }
    mock_get_db.return_value = mock_db
    mock_generate.return_value = ChatResponse(
        answer="the answer", citations=[], model="llama3.2", kb_id="kb-1"
    )

    result = endpoint_service.invoke_endpoint("ep-1", "what does clause 4 say?")

    assert result.answer == "the answer"
    mock_generate.assert_called_once()
    call_kwargs = mock_generate.call_args.kwargs
    assert call_kwargs["kb_id"] == "kb-1"
    assert call_kwargs["temperature"] == 0.2
    mock_db.endpoints.update_one.assert_called_once()


@patch("app.services.endpoint_service.get_mongo_db")
def test_invoke_endpoint_not_found(mock_get_db):
    mock_db = MagicMock()
    mock_db.endpoints.find_one.return_value = None
    mock_get_db.return_value = mock_db

    with pytest.raises(ValueError, match="not found"):
        endpoint_service.invoke_endpoint("missing-ep", "anything")