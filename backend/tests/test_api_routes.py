import json
import os
from datetime import date
from unittest.mock import AsyncMock, patch

# Set env vars BEFORE any app imports
os.environ["MONDAY_API_TOKEN"] = "test-token"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["USERS_CONFIG"] = json.dumps([
    {"email": "admin@test.com", "password": "pass", "role": "admin", "name": "Admin", "monday_user_id": "1"},
])

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import AuthService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_header():
    svc = AuthService(
        users_config=os.environ["USERS_CONFIG"],
        jwt_secret="test-secret",
    )
    user = svc.authenticate("admin@test.com", "pass")
    token = svc.create_token(user)
    return {"Authorization": f"Bearer {token}"}


# Mock data that sync_all returns
MOCK_WO_ITEMS = [
    {
        "id": "1", "name": "[開發]Test工單",
        "column_values": [
            {"id": "dropdown_mkkzznt3", "text": "JGB", "value": None, "type": "dropdown"},
            {"id": "color_mkxfd8jn", "text": "開發", "value": None, "type": "status"},
            {"id": "color_mkxfxqs2", "text": "Tuo", "value": None, "type": "status"},
            {"id": "color_mkxfagvd", "text": "Lenny", "value": None, "type": "status"},
            {"id": "color_mkxfdhzv", "text": "Robin", "value": None, "type": "status"},
            {"id": "color_mkxfk0mh", "text": "Robin", "value": None, "type": "status"},
            {"id": "color_mkxfvdj3", "text": "Robin", "value": None, "type": "status"},
            {"id": "date_mkxfdt3d", "text": "2026-05-01", "value": None, "type": "date"},
            {"id": "date_mkxfjy8s", "text": "2026-05-03", "value": None, "type": "date"},
            {"id": "date_mkxfyb3x", "text": "2026-05-04", "value": None, "type": "date"},
            {"id": "date_mkxfregq", "text": "2026-05-05", "value": None, "type": "date"},
            {"id": "pulse_id_mkxf8pt9", "text": "1", "value": None, "type": "item_id"},
        ],
    },
    {
        "id": "2", "name": "[臭蟲]Bug修復",
        "column_values": [
            {"id": "dropdown_mkkzznt3", "text": "富喬", "value": None, "type": "dropdown"},
            {"id": "color_mkxfd8jn", "text": "臭蟲", "value": None, "type": "status"},
            {"id": "color_mkxfxqs2", "text": "Jet", "value": None, "type": "status"},
            {"id": "color_mkxfagvd", "text": "Abu", "value": None, "type": "status"},
            {"id": "color_mkxfdhzv", "text": "", "value": None, "type": "status"},
            {"id": "color_mkxfk0mh", "text": "", "value": None, "type": "status"},
            {"id": "color_mkxfvdj3", "text": None, "value": None, "type": "status"},
            {"id": "date_mkxfdt3d", "text": "2026-05-10", "value": None, "type": "date"},
            {"id": "date_mkxfjy8s", "text": "", "value": None, "type": "date"},
            {"id": "date_mkxfyb3x", "text": "", "value": None, "type": "date"},
            {"id": "date_mkxfregq", "text": "", "value": None, "type": "date"},
            {"id": "pulse_id_mkxf8pt9", "text": "2", "value": None, "type": "item_id"},
        ],
    },
]

MOCK_CAMP_ITEMS = [
    {
        "id": "c1", "name": "FB_Post_1",
        "column_values": [
            {"id": "person", "text": "Alice", "value": None, "type": "people"},
            {"id": "color_mm0dy0by", "text": "Holiday", "value": None, "type": "status"},
            {"id": "date_mm0dmy4j", "text": "2026-03-01", "value": None, "type": "date"},
            {"id": "color_mm0dtqem", "text": "Direct-Go", "value": None, "type": "status"},
            {"id": "color_mm0gy6kv", "text": "Completed", "value": None, "type": "status"},
            {"id": "platform_1", "text": "Facebook", "value": None, "type": "status"},
            {"id": "boolean_mm1397yf", "text": "", "value": '{"checked":false}', "type": "checkbox"},
            {"id": "color_mm0fa2jj", "text": "ZH", "value": None, "type": "status"},
        ],
        "subitems": [],
        "group": {"id": "g1", "title": "FB｜JGB Smart Property"},
    },
]

MOCK_USERS = [
    {"id": "1", "name": "Lenny", "email": "lenny@test.com"},
    {"id": "2", "name": "Alice", "email": "alice@test.com"},
]

MOCK_SYNC_RESULT = {
    "work_orders": MOCK_WO_ITEMS,
    "campaigns": MOCK_CAMP_ITEMS,
    "users": MOCK_USERS,
}


def _mock_monday_service():
    from app.services.monday_api import MondayAPIService
    svc = MondayAPIService(api_token="test", cache_ttl=900)
    svc.sync_all = AsyncMock(return_value=MOCK_SYNC_RESULT)
    svc.clear_cache = lambda: None
    return svc


@pytest.fixture(autouse=True)
def _patch_sync():
    """Override the monday service singleton for all route tests."""
    from app.routers.data_deps import set_monday_service
    svc = _mock_monday_service()
    set_monday_service(svc)
    yield
    set_monday_service(None)  # type: ignore


# === Workload routes ===

class TestWorkloadRoutes:
    def test_team(self, client, auth_header):
        resp = client.get("/api/workload/team", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_tasks"] == 2
        assert data["department"] == "pm_rd"

    def test_team_with_department(self, client, auth_header):
        resp = client.get("/api/workload/team?department=marketing", headers=auth_header)
        assert resp.status_code == 200

    def test_member(self, client, auth_header):
        resp = client.get("/api/workload/member/Lenny", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["workload"]["user_name"] == "Lenny"

    def test_requires_auth(self, client):
        resp = client.get("/api/workload/team")
        assert resp.status_code == 401


# === Efficiency routes ===

class TestEfficiencyRoutes:
    def test_overview(self, client, auth_header):
        resp = client.get("/api/efficiency/overview", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "efficiency" in data
        assert "by_type" in data

    def test_stalled(self, client, auth_header):
        resp = client.get("/api/efficiency/stalled", headers=auth_header)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_trends(self, client, auth_header):
        resp = client.get("/api/efficiency/trends", headers=auth_header)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# === Schedule routes ===

class TestScheduleRoutes:
    def test_gantt(self, client, auth_header):
        resp = client.get("/api/schedule/gantt", headers=auth_header)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_heatmap_person(self, client, auth_header):
        resp = client.get("/api/schedule/heatmap/person", headers=auth_header)
        assert resp.status_code == 200

    def test_heatmap_client(self, client, auth_header):
        resp = client.get("/api/schedule/heatmap/client", headers=auth_header)
        assert resp.status_code == 200

    def test_aging(self, client, auth_header):
        resp = client.get("/api/schedule/aging", headers=auth_header)
        assert resp.status_code == 200

    def test_calendar(self, client, auth_header):
        resp = client.get("/api/schedule/calendar", headers=auth_header)
        assert resp.status_code == 200


# === Quality routes ===

class TestQualityRoutes:
    def test_overview(self, client, auth_header):
        resp = client.get("/api/quality/overview", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "bug_recurrence" in data

    def test_bug_recurrence(self, client, auth_header):
        resp = client.get("/api/quality/bug-recurrence", headers=auth_header)
        assert resp.status_code == 200


# === Sync routes ===

class TestSyncRoutes:
    def test_sync_post(self, client, auth_header):
        resp = client.post("/api/sync", headers=auth_header)
        assert resp.status_code == 200
        assert "last_sync_time" in resp.json()

    def test_sync_status(self, client, auth_header):
        resp = client.get("/api/sync/status", headers=auth_header)
        assert resp.status_code == 200


# === Users route ===

class TestUsersRoute:
    def test_get_users(self, client, auth_header):
        resp = client.get("/api/users", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 2
