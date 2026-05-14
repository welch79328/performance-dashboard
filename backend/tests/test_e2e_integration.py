"""
End-to-end integration test.
Uses actual Monday.com API to verify full data pipeline.
Run with: pytest tests/test_e2e_integration.py -v -s
Requires MONDAY_API_TOKEN in .env
"""
import json
import os

import pytest

# Set test env before imports
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("USERS_CONFIG", json.dumps([
    {"email": "admin@test.com", "password": "pass", "role": "admin", "name": "Admin", "monday_user_id": "1"},
]))

from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_service import AuthService

# Skip all tests if no real API token
REAL_TOKEN = os.environ.get("MONDAY_API_TOKEN", "")
HAS_REAL_TOKEN = REAL_TOKEN and REAL_TOKEN != "test-token" and REAL_TOKEN != "your-monday-api-token-here"
skip_no_token = pytest.mark.skipif(not HAS_REAL_TOKEN, reason="No real MONDAY_API_TOKEN")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_header():
    svc = AuthService(
        users_config=os.environ.get("USERS_CONFIG", "[]"),
        jwt_secret=os.environ.get("JWT_SECRET", "test"),
    )
    user = svc.authenticate("admin@test.com", "pass")
    if not user:
        pytest.skip("Cannot authenticate")
    return {"Authorization": f"Bearer {svc.create_token(user)}"}


@skip_no_token
class TestE2EWithRealAPI:
    """These tests call the real Monday.com API — run sparingly."""

    def test_sync_and_workload(self, client, auth_header):
        """Full pipeline: sync → parse → calculate workload."""
        # Trigger sync
        resp = client.post("/api/sync", headers=auth_header)
        assert resp.status_code == 200
        assert "last_sync_time" in resp.json()

        # Get team workload
        resp = client.get("/api/workload/team?department=pm_rd", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_tasks"] > 0
        assert data["department"] == "pm_rd"
        print(f"\n  工單總表: {data['total_tasks']} 筆, 結案率: {data['close_rate']}%")

    def test_efficiency_overview(self, client, auth_header):
        resp = client.get("/api/efficiency/overview", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "efficiency" in data
        assert "by_type" in data
        eff = data["efficiency"]
        print(f"\n  平均處理天數: {eff['avg_total_days']}, 結案率: {eff['close_rate']}%")
        for bt in data["by_type"]:
            print(f"    {bt['type_name']}: {bt['count']}筆, 平均{bt['avg_total_days']}天")

    def test_schedule_gantt(self, client, auth_header):
        resp = client.get("/api/schedule/gantt", headers=auth_header)
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        print(f"\n  甘特圖工單數: {len(items)}")

    def test_schedule_aging(self, client, auth_header):
        resp = client.get("/api/schedule/aging", headers=auth_header)
        assert resp.status_code == 200
        aging = resp.json()
        red = sum(1 for a in aging if a["severity"] == "red")
        yellow = sum(1 for a in aging if a["severity"] == "yellow")
        green = sum(1 for a in aging if a["severity"] == "green")
        print(f"\n  老化表: 紅{red} 黃{yellow} 綠{green}, 共{len(aging)}筆未結案")

    def test_quality_overview(self, client, auth_header):
        resp = client.get("/api/quality/overview", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        print(f"\n  異動密集度: {data['change_density']}%")
        if data["bug_recurrence"]:
            top = list(data["bug_recurrence"].items())[:3]
            print(f"  Bug回流前3: {top}")

    def test_users_list(self, client, auth_header):
        resp = client.get("/api/users", headers=auth_header)
        assert resp.status_code == 200
        users = resp.json()
        assert len(users) > 0
        print(f"\n  使用者數: {len(users)}")
        for u in users[:5]:
            print(f"    {u['name']} ({u['email']})")

    def test_member_workload(self, client, auth_header):
        resp = client.get("/api/workload/member/Lenny", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        wl = data["workload"]
        print(f"\n  Lenny: PM={wl['pm_count']} 開發={wl['dev_count']} 測試={wl['test_count']} 在手={wl['in_progress_count']}")

    def test_trends(self, client, auth_header):
        resp = client.get("/api/efficiency/trends?weeks=4", headers=auth_header)
        assert resp.status_code == 200
        trends = resp.json()
        assert len(trends) == 4
        for t in trends:
            print(f"\n  {t['week_start']}: {t['task_count']}筆, 結案率{t['close_rate']}%")

    def test_export_weekly(self, client, auth_header):
        resp = client.get("/api/export/weekly", headers=auth_header)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(resp.content) > 1000  # Should be a real xlsx
        print(f"\n  週報 Excel: {len(resp.content)} bytes")

    def test_marketing_calendar(self, client, auth_header):
        resp = client.get("/api/schedule/calendar", headers=auth_header)
        assert resp.status_code == 200
        campaigns = resp.json()
        print(f"\n  行銷活動數: {len(campaigns)}")

    def test_auth_flow(self, client):
        # Login
        resp = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "pass"})
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # Me
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

        # Unauthorized
        resp = client.get("/api/workload/team")
        assert resp.status_code == 401
