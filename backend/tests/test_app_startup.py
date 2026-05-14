from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_swagger_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_settings_load_env():
    from app.config.settings import Settings

    s = Settings(monday_api_token="test-token", jwt_secret="test-secret")
    assert s.monday_api_token == "test-token"
    assert s.jwt_secret == "test-secret"
    assert s.cache_ttl_seconds == 900
