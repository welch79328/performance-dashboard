import json

import pytest
from fastapi.testclient import TestClient

from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    users_config = json.dumps([
        {"email": "admin@jgbsmart.com", "password": "admin123", "role": "admin", "name": "Admin", "monday_user_id": "1"},
        {"email": "lenny@jgbsmart.com", "password": "lenny123", "role": "member", "name": "Lenny", "monday_user_id": "2"},
    ])
    return AuthService(
        users_config=users_config,
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expire_minutes=60,
    )


# === AuthService unit tests ===

class TestAuthenticate:
    def test_valid_credentials(self, auth_service):
        user = auth_service.authenticate("admin@jgbsmart.com", "admin123")
        assert user is not None
        assert user["name"] == "Admin"
        assert user["role"] == "admin"

    def test_invalid_password(self, auth_service):
        user = auth_service.authenticate("admin@jgbsmart.com", "wrong")
        assert user is None

    def test_invalid_email(self, auth_service):
        user = auth_service.authenticate("nobody@test.com", "admin123")
        assert user is None


class TestJWT:
    def test_create_and_verify_token(self, auth_service):
        user = {"email": "admin@jgbsmart.com", "role": "admin", "name": "Admin", "monday_user_id": "1"}
        token = auth_service.create_token(user)
        assert isinstance(token, str)

        decoded = auth_service.verify_token(token)
        assert decoded["email"] == "admin@jgbsmart.com"
        assert decoded["role"] == "admin"

    def test_invalid_token(self, auth_service):
        result = auth_service.verify_token("invalid.token.here")
        assert result is None

    def test_token_contains_role(self, auth_service):
        user = {"email": "lenny@jgbsmart.com", "role": "member", "name": "Lenny", "monday_user_id": "2"}
        token = auth_service.create_token(user)
        decoded = auth_service.verify_token(token)
        assert decoded["role"] == "member"
        assert decoded["monday_user_id"] == "2"


# === API endpoint tests ===

class TestAuthEndpoints:
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_login_success(self, client):
        response = client.post("/api/auth/login", json={
            "email": "admin@test.com", "password": "pass"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["name"] == "Admin"
        assert data["user"]["role"] == "admin"

    def test_login_failure(self, client):
        response = client.post("/api/auth/login", json={
            "email": "admin@test.com", "password": "wrong"
        })
        assert response.status_code == 401

    def test_me_with_token(self, client):
        login_resp = client.post("/api/auth/login", json={
            "email": "admin@test.com", "password": "pass"
        })
        token = login_resp.json()["access_token"]
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert response.json()["email"] == "admin@test.com"

    def test_me_without_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, client):
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid.token"
        })
        assert response.status_code == 401
