from unittest.mock import patch

from app.schemas.hyperparameters import GlobalConfigResponse


@patch("app.api.config.config_service.get_global_config")
def test_get_config_endpoint(mock_get, authenticated_client):
    mock_get.return_value = GlobalConfigResponse(
        model="llama3.2", temperature=0.7, top_k=5, chunk_size=500, chunk_overlap=50, preamble="Be helpful."
    )
    response = authenticated_client.get("/config")
    assert response.status_code == 200
    assert response.json()["temperature"] == 0.7


def test_config_requires_auth(client):
    response = client.get("/config")
    assert response.status_code == 401