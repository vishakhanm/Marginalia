from unittest.mock import patch

from app.schemas.history import ConversationListResponse


@patch("app.api.history.history_service.list_conversations")
def test_list_conversations_endpoint(mock_list, authenticated_client):
    mock_list.return_value = ConversationListResponse(conversations=[], count=0)
    response = authenticated_client.get("/history")
    assert response.status_code == 200
    assert response.json()["count"] == 0


@patch("app.api.history.history_service.get_conversation")
def test_get_conversation_endpoint_not_found(mock_get, authenticated_client):
    mock_get.return_value = None
    response = authenticated_client.get("/history/missing-id")
    assert response.status_code == 404


def test_list_conversations_requires_auth(client):
    response = client.get("/history")
    assert response.status_code == 401