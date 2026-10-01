from unittest.mock import patch

from app.schemas.rag import ChatResponse, Citation
from app.schemas.history import ConversationInfo
from datetime import datetime, timezone


def _fake_conversation():
    now = datetime.now(timezone.utc)
    return ConversationInfo(
        id="conv-1", user_id="user-1", kb_id="kb-1", title="What is...", created_at=now, updated_at=now
    )


@patch("app.api.chat.history_service.save_exchange")
@patch("app.api.chat.rag_service.generate_answer")
def test_chat_endpoint_success(mock_generate, mock_save, authenticated_client):
    mock_generate.return_value = ChatResponse(
        answer="Paris is the capital of France.",
        citations=[
            Citation(
                document_id="doc-1", filename="notes.txt", chunk_index=0,
                text_snippet="Paris is the capital of France.", score=0.95,
            )
        ],
        model="llama3.2",
        kb_id="kb-1",
    )
    mock_save.return_value = _fake_conversation()

    response = authenticated_client.post(
        "/chat", json={"kb_id": "kb-1", "query": "What is the capital of France?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "Paris" in body["answer"]
    assert body["conversation_id"] == "conv-1"
    mock_save.assert_called_once()


@patch("app.api.chat.rag_service.generate_answer")
def test_chat_endpoint_kb_not_found(mock_generate, authenticated_client):
    mock_generate.side_effect = ValueError("Knowledge base 'missing-kb' not found")
    response = authenticated_client.post("/chat", json={"kb_id": "missing-kb", "query": "anything"})
    assert response.status_code == 404


def test_chat_endpoint_requires_auth(client):
    """Without the auth override, /chat should reject the request."""
    response = client.post("/chat", json={"kb_id": "kb-1", "query": "anything"})
    assert response.status_code == 401