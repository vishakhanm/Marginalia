from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.model import ModelListResponse, ModelInfo, PullModelResponse

client = TestClient(app)


@patch("app.api.models.model_service.list_models")
def test_get_models_endpoint(mock_list):
    mock_list.return_value = ModelListResponse(
        models=[ModelInfo(name="llama3.2:latest")], count=1
    )
    response = client.get("/models")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["models"][0]["name"] == "llama3.2:latest"


@patch("app.api.models.model_service.pull_model")
def test_pull_model_endpoint_success(mock_pull):
    mock_pull.return_value = PullModelResponse(name="llama3.2", status="success")
    response = client.post("/models/pull", json={"name": "llama3.2"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@patch("app.api.models.model_service.pull_model")
def test_pull_model_endpoint_failure(mock_pull):
    mock_pull.return_value = PullModelResponse(
        name="bad-model", status="error", detail="not found"
    )
    response = client.post("/models/pull", json={"name": "bad-model"})
    assert response.status_code == 502