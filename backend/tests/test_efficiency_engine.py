import math
from datetime import date, timedelta

import pytest

from app.models.work_order import WorkOrder
from app.models.campaign import Campaign
from app.services.efficiency_engine import (
    calculate_efficiency,
    calculate_efficiency_by_type,
    find_stalled_orders,
    calculate_weekly_trends,
    calculate_marketing_efficiency,
)


def _wo(id: str, type: str = "開發", assign: str | None = "2026-05-01",
        test_date: str | None = None, close: str | None = None,
        dev: str = "Lenny", client: str = "JGB") -> WorkOrder:
    return WorkOrder(
        id=id, name=f"WO-{id}", type=type, developer=dev, client=client,
        assign_date=date.fromisoformat(assign) if assign else None,
        test_assign_date=date.fromisoformat(test_date) if test_date else None,
        close_date=date.fromisoformat(close) if close else None,
    )


def _camp(id: str, status: str = "Completed", pub_date: str | None = "2026-03-01",
          owner: str = "Alice") -> Campaign:
    return Campaign(
        id=id, name=f"Post-{id}", owner=owner,
        completion_status=status,
        publish_date=date.fromisoformat(pub_date) if pub_date else None,
    )


# === Efficiency metrics ===

class TestCalculateEfficiency:
    def test_avg_total_days(self):
        orders = [
            _wo("1", assign="2026-05-01", close="2026-05-03"),  # 2 days
            _wo("2", assign="2026-05-01", close="2026-05-05"),  # 4 days
        ]
        em = calculate_efficiency(orders)
        assert em.avg_total_days == 3.0

    def test_avg_dev_days(self):
        orders = [
            _wo("1", assign="2026-05-01", test_date="2026-05-02"),  # 1 day
            _wo("2", assign="2026-05-01", test_date="2026-05-04"),  # 3 days
        ]
        em = calculate_efficiency(orders)
        assert em.avg_dev_days == 2.0

    def test_avg_test_days(self):
        orders = [
            _wo("1", test_date="2026-05-03", close="2026-05-04"),  # 1 day
            _wo("2", test_date="2026-05-03", close="2026-05-06"),  # 3 days
        ]
        em = calculate_efficiency(orders)
        assert em.avg_test_days == 2.0

    def test_close_rate(self):
        orders = [
            _wo("1", close="2026-05-03"),
            _wo("2", close="2026-05-05"),
            _wo("3"),  # not closed
        ]
        em = calculate_efficiency(orders)
        assert em.close_rate == pytest.approx(66.67, abs=0.1)

    def test_stalled_rate(self):
        orders = [
            _wo("1", assign="2026-05-01", test_date="2026-05-02"),  # ok
            _wo("2", assign="2026-04-20"),  # stalled >7 days, no test date
            _wo("3", assign="2026-04-25"),  # stalled >7 days
        ]
        em = calculate_efficiency(orders, today=date(2026, 5, 10))
        assert em.stalled_rate == pytest.approx(66.67, abs=0.1)
        assert len(em.stalled_orders) == 2

    def test_empty_orders(self):
        em = calculate_efficiency([])
        assert em.avg_total_days == 0
        assert em.close_rate == 0
        assert em.stalled_rate == 0


# === Efficiency by type ===

class TestEfficiencyByType:
    def test_groups_by_type(self):
        orders = [
            _wo("1", type="異動", assign="2026-05-01", close="2026-05-01"),  # 0 days
            _wo("2", type="異動", assign="2026-05-02", close="2026-05-02"),  # 0 days
            _wo("3", type="開發", assign="2026-05-01", close="2026-05-06"),  # 5 days
            _wo("4", type="臭蟲", assign="2026-05-01", close="2026-05-03"),  # 2 days
        ]
        by_type = calculate_efficiency_by_type(orders)
        type_map = {t.type_name: t for t in by_type}

        assert type_map["異動"].avg_total_days == 0.0
        assert type_map["異動"].count == 2
        assert type_map["開發"].avg_total_days == 5.0
        assert type_map["臭蟲"].avg_total_days == 2.0

    def test_close_rate_per_type(self):
        orders = [
            _wo("1", type="開發", close="2026-05-05"),
            _wo("2", type="開發"),  # not closed
        ]
        by_type = calculate_efficiency_by_type(orders)
        dev = [t for t in by_type if t.type_name == "開發"][0]
        assert dev.close_rate == 50.0


# === Stalled orders ===

class TestFindStalledOrders:
    def test_finds_stalled(self):
        orders = [
            _wo("1", assign="2026-05-01", test_date="2026-05-02"),  # not stalled
            _wo("2", assign="2026-04-20"),  # stalled
            _wo("3", assign="2026-05-01", close="2026-05-03"),  # closed, not stalled
        ]
        stalled = find_stalled_orders(orders, threshold_days=7, today=date(2026, 5, 10))
        assert len(stalled) == 1
        assert stalled[0].id == "2"
        assert stalled[0].severity == "red"
        assert stalled[0].days_open == 20

    def test_severity_levels(self):
        orders = [
            _wo("1", assign="2026-05-08"),  # 2 days = green (but not stalled, <7)
            _wo("2", assign="2026-05-05"),  # 5 days = yellow (but not stalled, <7)
            _wo("3", assign="2026-05-01"),  # 9 days = red
        ]
        stalled = find_stalled_orders(orders, threshold_days=7, today=date(2026, 5, 10))
        assert len(stalled) == 1  # only >7 days
        assert stalled[0].severity == "red"

    def test_no_assign_date_excluded(self):
        orders = [_wo("1", assign=None)]
        stalled = find_stalled_orders(orders, today=date(2026, 5, 10))
        assert len(stalled) == 0


# === Weekly trends ===

class TestWeeklyTrends:
    def test_trend_count(self):
        orders = [
            _wo("1", assign="2026-04-28", close="2026-04-29"),
            _wo("2", assign="2026-05-05", close="2026-05-06"),
            _wo("3", assign="2026-05-05"),
        ]
        trends = calculate_weekly_trends(orders, weeks=4, today=date(2026, 5, 14))
        assert len(trends) == 4

    def test_trend_task_count_per_week(self):
        orders = [
            _wo("1", assign="2026-05-05"),
            _wo("2", assign="2026-05-06"),
            _wo("3", assign="2026-05-12"),
        ]
        trends = calculate_weekly_trends(orders, weeks=2, today=date(2026, 5, 14))
        # Most recent week (5/12-5/18) should have 1 order
        # Previous week (5/5-5/11) should have 2 orders
        total_tasks = sum(t.task_count for t in trends)
        assert total_tasks == 3

    def test_empty_weeks(self):
        trends = calculate_weekly_trends([], weeks=4, today=date(2026, 5, 14))
        assert len(trends) == 4
        assert all(t.task_count == 0 for t in trends)


# === Marketing efficiency ===

class TestMarketingEfficiency:
    def test_completion_rate(self):
        campaigns = [
            _camp("1", status="Completed"),
            _camp("2", status="Completed"),
            _camp("3", status="Scheduled"),
            _camp("4", status="Paused"),
        ]
        me = calculate_marketing_efficiency(campaigns)
        assert me.completion_rate == 50.0

    def test_weekly_std_dev(self):
        # All posts in one week = std_dev 0 (if only 1 week data)
        campaigns = [
            _camp("1", pub_date="2026-03-01"),
            _camp("2", pub_date="2026-03-02"),
        ]
        me = calculate_marketing_efficiency(campaigns)
        # Should have a numeric std_dev
        assert isinstance(me.weekly_std_dev, float)

    def test_material_completeness(self):
        from app.models.campaign import CampaignSubitem
        c1 = Campaign(
            id="1", name="post1",
            subitems=[
                CampaignSubitem(id="s1", name="Copy", status="Done"),
                CampaignSubitem(id="s2", name="Visual", status="Done"),
            ],
        )
        c2 = Campaign(
            id="2", name="post2",
            subitems=[
                CampaignSubitem(id="s3", name="Copy", status="Done"),
                CampaignSubitem(id="s4", name="Visual", status="未指定"),
            ],
        )
        me = calculate_marketing_efficiency([c1, c2])
        assert me.material_completeness == 75.0  # (100 + 50) / 2

    def test_empty_campaigns(self):
        me = calculate_marketing_efficiency([])
        assert me.completion_rate == 0
        assert me.weekly_std_dev == 0
        assert me.material_completeness == 0
