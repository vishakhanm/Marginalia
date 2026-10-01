from unittest.mock import patch
from datetime import datetime, timezone

from app.schemas.endpoint import EndpointInfo
from app.schemas.rag import ChatResponse


@patch("app.api.endpoints.endpoint_service.create_endpoint")
def test_create_endpoint_api(mock_create, authenticated_client):
    mock_create.return_value = EndpointInfo(
        id="ep-1", name="legal-qa", kb_id="kb-1", hyperparameters=None,
        created_at=datetime.now(timezone.utc), call_count=0,
    )
    response = authenticated_client.post("/endpoints", json={"name": "legal-qa", "kb_id": "kb-1"})
    assert response.status_code == 200


def test_endpoints_management_requires_auth(client):
    response = client.get("/endpoints")
    assert response.status_code == 401


@patch("app.api.inference.endpoint_service.invoke_endpoint")
def test_invoke_endpoint_api_is_public(mock_invoke, client):
    """The /inference route stays public — external consumers shouldn't need platform auth."""
    mock_invoke.return_value = ChatResponse(answer="the answer", citations=[], model="llama3.2", kb_id="kb-1")
    response = client.post("/inference/ep-1", json={"query": "what does clause 4 say?"})
    assert response.status_code == 200