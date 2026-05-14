from datetime import date

import pytest

from app.models.work_order import WorkOrder
from app.models.campaign import Campaign, CampaignSubitem
from app.services.quality_engine import (
    calculate_bug_recurrence,
    calculate_change_density,
    calculate_material_completeness_avg,
)


def _wo(id: str, type: str = "開發", client: str = "JGB",
        assign: str | None = "2026-05-01") -> WorkOrder:
    return WorkOrder(
        id=id, name=f"WO-{id}", type=type, client=client,
        assign_date=date.fromisoformat(assign) if assign else None,
    )


# === Bug recurrence ===

class TestBugRecurrence:
    def test_counts_bugs_per_client(self):
        orders = [
            _wo("1", type="臭蟲", client="JGB"),
            _wo("2", type="臭蟲", client="JGB"),
            _wo("3", type="臭蟲", client="富喬"),
            _wo("4", type="開發", client="JGB"),  # not a bug
        ]
        result = calculate_bug_recurrence(orders)
        assert result["JGB"] == 2
        assert result["富喬"] == 1
        assert "開發" not in result.values()

    def test_no_bugs(self):
        orders = [_wo("1", type="開發"), _wo("2", type="異動")]
        result = calculate_bug_recurrence(orders)
        assert len(result) == 0

    def test_empty_orders(self):
        result = calculate_bug_recurrence([])
        assert result == {}

    def test_sorted_by_count_desc(self):
        orders = [
            _wo("1", type="臭蟲", client="A"),
            _wo("2", type="臭蟲", client="B"),
            _wo("3", type="臭蟲", client="B"),
            _wo("4", type="臭蟲", client="B"),
        ]
        result = calculate_bug_recurrence(orders)
        keys = list(result.keys())
        assert keys[0] == "B"
        assert result["B"] == 3


# === Change density ===

class TestChangeDensity:
    def test_overall_density(self):
        orders = [
            _wo("1", type="異動"),
            _wo("2", type="異動"),
            _wo("3", type="開發"),
            _wo("4", type="臭蟲"),
        ]
        qm = calculate_change_density(orders, weeks=4, today=date(2026, 5, 14))
        assert qm.change_density == 50.0  # 2/4 = 50%

    def test_zero_density(self):
        orders = [_wo("1", type="開發"), _wo("2", type="臭蟲")]
        qm = calculate_change_density(orders, weeks=4, today=date(2026, 5, 14))
        assert qm.change_density == 0.0

    def test_trend_has_weekly_entries(self):
        orders = [
            _wo("1", type="異動", assign="2026-05-05"),
            _wo("2", type="開發", assign="2026-05-05"),
            _wo("3", type="異動", assign="2026-05-12"),
        ]
        qm = calculate_change_density(orders, weeks=4, today=date(2026, 5, 14))
        assert len(qm.change_density_trend) == 4

    def test_empty_orders(self):
        qm = calculate_change_density([], weeks=4, today=date(2026, 5, 14))
        assert qm.change_density == 0
        assert len(qm.change_density_trend) == 4
        assert all(v == 0 for v in qm.change_density_trend)

    def test_bug_recurrence_included(self):
        orders = [
            _wo("1", type="臭蟲", client="JGB"),
            _wo("2", type="臭蟲", client="JGB"),
        ]
        qm = calculate_change_density(orders, weeks=4, today=date(2026, 5, 14))
        assert qm.bug_recurrence["JGB"] == 2


# === Material completeness ===

class TestMaterialCompleteness:
    def test_all_complete(self):
        campaigns = [
            Campaign(id="1", name="p1", subitems=[
                CampaignSubitem(id="s1", name="Copy", status="Done"),
                CampaignSubitem(id="s2", name="Visual", status="Done"),
            ]),
        ]
        assert calculate_material_completeness_avg(campaigns) == 100.0

    def test_partial(self):
        campaigns = [
            Campaign(id="1", name="p1", subitems=[
                CampaignSubitem(id="s1", name="Copy", status="Done"),
                CampaignSubitem(id="s2", name="Visual", status="未指定"),
            ]),
            Campaign(id="2", name="p2", subitems=[
                CampaignSubitem(id="s3", name="Copy", status="Done"),
                CampaignSubitem(id="s4", name="Visual", status="Done"),
            ]),
        ]
        assert calculate_material_completeness_avg(campaigns) == 75.0

    def test_no_subitems(self):
        campaigns = [Campaign(id="1", name="p1")]
        assert calculate_material_completeness_avg(campaigns) == 0

    def test_empty(self):
        assert calculate_material_completeness_avg([]) == 0
