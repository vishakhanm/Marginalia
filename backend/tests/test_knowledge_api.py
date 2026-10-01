from unittest.mock import patch
from datetime import datetime, timezone

from app.schemas.knowledge import KnowledgeBaseInfo


@patch("app.api.knowledge.kb_service.create_knowledge_base")
def test_create_knowledge_base_endpoint(mock_create, authenticated_client):
    mock_create.return_value = KnowledgeBaseInfo(
        id="kb-1", name="My KB", description=None,
        created_at=datetime.now(timezone.utc), document_count=0, chunk_count=0,
    )
    response = authenticated_client.post("/knowledge", json={"name": "My KB"})
    assert response.status_code == 200
    assert response.json()["name"] == "My KB"


@patch("app.api.knowledge.kb_service.get_knowledge_base")
def test_get_knowledge_base_not_found(mock_get, authenticated_client):
    mock_get.return_value = None
    response = authenticated_client.get("/knowledge/nonexistent-id")
    assert response.status_code == 404


def test_knowledge_requires_auth(client):
    response = client.get("/knowledge")
    assert response.status_code == 401