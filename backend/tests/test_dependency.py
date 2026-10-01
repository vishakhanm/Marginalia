from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dependency_health_check():
    """
    This test requires Qdrant and MongoDB to be running
    (docker compose up -d) — it's an integration check, not a unit test.
    """
    response = client.get("/health/dependencies")
    assert response.status_code == 200
    body = response.json()
    assert "dependencies" in body
    assert body["dependencies"]["mongo"] == "ok"
    assert body["dependencies"]["qdrant"] == "ok"