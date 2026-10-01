from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.services import history_service
from app.schemas.rag import ChatResponse


@patch("app.services.history_service.get_mongo_db")
def test_save_exchange_creates_new_conversation(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    response = ChatResponse(answer="Paris is the capital.", citations=[], model="llama3.2", kb_id="kb-1")
    conversation = history_service.save_exchange(
        user_id="user-1", kb_id="kb-1", conversation_id=None,
        query="What is the capital of France?", response=response,
    )

    assert conversation.user_id == "user-1"
    assert conversation.title.startswith("What is the capital")
    assert mock_db.conversations.insert_one.call_count == 1
    assert mock_db.messages.insert_one.call_count == 2  # user + assistant


@patch("app.services.history_service.get_mongo_db")
def test_save_exchange_continues_existing_conversation(mock_get_db):
    mock_db = MagicMock()
    mock_db.conversations.find_one.return_value = {
        "_id": "conv-1", "user_id": "user-1", "kb_id": "kb-1", "title": "Existing chat",
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    }
    mock_get_db.return_value = mock_db

    response = ChatResponse(answer="Follow-up answer.", citations=[], model="llama3.2", kb_id="kb-1")
    conversation = history_service.save_exchange(
        user_id="user-1", kb_id="kb-1", conversation_id="conv-1",
        query="follow-up question", response=response,
    )

    assert conversation.id == "conv-1"
    mock_db.conversations.insert_one.assert_not_called()
    assert mock_db.messages.insert_one.call_count == 2


@patch("app.services.history_service.get_mongo_db")
def test_save_exchange_ignores_conversation_id_from_another_user(mock_get_db):
    """A conversation_id that doesn't belong to this user should be treated as absent, not reused."""
    mock_db = MagicMock()
    mock_db.conversations.find_one.return_value = None  # query filters by user_id too
    mock_get_db.return_value = mock_db

    response = ChatResponse(answer="answer", citations=[], model="llama3.2", kb_id="kb-1")
    conversation = history_service.save_exchange(
        user_id="user-1", kb_id="kb-1", conversation_id="someone-elses-conv",
        query="a question", response=response,
    )

    mock_db.conversations.insert_one.assert_called_once()  # a NEW conversation was created
    assert conversation.id != "someone-elses-conv"


@patch("app.services.history_service.get_mongo_db")
def test_get_conversation_wrong_owner_returns_none(mock_get_db):
    mock_db = MagicMock()
    mock_db.conversations.find_one.return_value = None
    mock_get_db.return_value = mock_db

    result = history_service.get_conversation("conv-1", user_id="someone-else")
    assert result is None


@patch("app.services.history_service.get_mongo_db")
def test_list_conversations(mock_get_db):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = [
        {
            "_id": "conv-1", "user_id": "user-1", "kb_id": "kb-1", "title": "Chat 1",
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
        }
    ]
    mock_db.conversations.find.return_value = mock_cursor
    mock_get_db.return_value = mock_db

    result = history_service.list_conversations("user-1")

    assert result.count == 1
    assert result.conversations[0].id == "conv-1"