from datetime import date

from app.models.work_order import WorkOrder
from app.models.campaign import Campaign, CampaignSubitem
from app.services.workload_engine import (
    calculate_person_workload,
    calculate_team_workload,
    calculate_marketing_workload,
    calculate_client_distribution,
    calculate_type_distribution,
    filter_by_date_range,
)


# === Test data helpers ===

def _wo(id: str, pm: str = "Tuo", dev: str = "Lenny", tester: str = "Robin",
        type: str = "開發", client: str = "JGB",
        assign: str | None = "2026-05-01", close: str | None = None,
        test_date: str | None = None) -> WorkOrder:
    return WorkOrder(
        id=id, name=f"WO-{id}", pm=pm, developer=dev, tester=tester,
        type=type, client=client,
        assign_date=date.fromisoformat(assign) if assign else None,
        test_assign_date=date.fromisoformat(test_date) if test_date else None,
        close_date=date.fromisoformat(close) if close else None,
    )


def _camp(id: str, owner: str = "Alice", group: str = "FB｜JGB Smart Property",
          content_type: str = "Holiday", pub_date: str | None = "2026-03-01",
          status: str = "Completed") -> Campaign:
    return Campaign(
        id=id, name=f"Post-{id}", owner=owner, group_name=group,
        content_type=content_type,
        publish_date=date.fromisoformat(pub_date) if pub_date else None,
        completion_status=status,
    )


# === 4.1 PM+RD workload ===

class TestPersonWorkload:
    def test_three_role_counts(self):
        orders = [
            _wo("1", pm="Tuo", dev="Lenny", tester="Robin"),
            _wo("2", pm="Tuo", dev="Lenny", tester="Tuo"),
            _wo("3", pm="Jet", dev="Abu", tester="Robin"),
        ]
        wl = calculate_person_workload(orders, "Tuo")
        assert wl.pm_count == 2
        assert wl.dev_count == 0
        assert wl.test_count == 1
        assert wl.total_count == 3

    def test_developer_workload(self):
        orders = [
            _wo("1", dev="Lenny"),
            _wo("2", dev="Lenny"),
            _wo("3", dev="Abu"),
        ]
        wl = calculate_person_workload(orders, "Lenny")
        assert wl.dev_count == 2
        assert wl.total_count == 2

    def test_in_progress_count(self):
        orders = [
            _wo("1", dev="Lenny", assign="2026-05-01", close="2026-05-03"),  # 已結案
            _wo("2", dev="Lenny", assign="2026-05-05"),                       # 開發中
            _wo("3", dev="Lenny", assign="2026-05-06", test_date="2026-05-07"),  # 測試中
        ]
        wl = calculate_person_workload(orders, "Lenny")
        assert wl.in_progress_count == 2

    def test_person_not_found(self):
        orders = [_wo("1", pm="Tuo", dev="Lenny", tester="Robin")]
        wl = calculate_person_workload(orders, "Nobody")
        assert wl.total_count == 0

    def test_multi_role_same_person(self):
        orders = [_wo("1", pm="Robin", dev="Robin", tester="Robin")]
        wl = calculate_person_workload(orders, "Robin")
        assert wl.pm_count == 1
        assert wl.dev_count == 1
        assert wl.test_count == 1
        assert wl.total_count == 3


class TestTeamWorkload:
    def test_team_totals(self):
        orders = [
            _wo("1", close="2026-05-03"),
            _wo("2"),
            _wo("3", close="2026-05-05"),
        ]
        team = calculate_team_workload(orders)
        assert team.total_tasks == 3
        assert team.completed_tasks == 2
        assert team.in_progress_tasks == 1
        assert team.close_rate == pytest.approx(66.67, abs=0.1)

    def test_empty_orders(self):
        team = calculate_team_workload([])
        assert team.total_tasks == 0
        assert team.close_rate == 0


class TestDistributions:
    def test_client_distribution(self):
        orders = [
            _wo("1", client="JGB"),
            _wo("2", client="JGB"),
            _wo("3", client="富喬"),
        ]
        dist = calculate_client_distribution(orders)
        assert dist["JGB"] == 2
        assert dist["富喬"] == 1

    def test_type_distribution(self):
        orders = [
            _wo("1", type="開發"),
            _wo("2", type="臭蟲"),
            _wo("3", type="開發"),
        ]
        dist = calculate_type_distribution(orders)
        assert dist["開發"] == 2
        assert dist["臭蟲"] == 1


class TestDateFilter:
    def test_filter_by_assign_date(self):
        orders = [
            _wo("1", assign="2026-04-15"),
            _wo("2", assign="2026-05-01"),
            _wo("3", assign="2026-05-10"),
        ]
        filtered = filter_by_date_range(orders, date(2026, 5, 1), date(2026, 5, 31))
        assert len(filtered) == 2
        assert filtered[0].id == "2"

    def test_filter_no_assign_date_excluded(self):
        orders = [
            _wo("1", assign=None),
            _wo("2", assign="2026-05-01"),
        ]
        filtered = filter_by_date_range(orders, date(2026, 5, 1), date(2026, 5, 31))
        assert len(filtered) == 1


# === 4.2 Marketing workload ===

class TestMarketingWorkload:
    def test_content_count(self):
        campaigns = [_camp("1"), _camp("2"), _camp("3")]
        wl = calculate_marketing_workload(campaigns, "Alice")
        assert wl.content_count == 3

    def test_platform_distribution_by_group(self):
        campaigns = [
            _camp("1", group="FB｜JGB Smart Property"),
            _camp("2", group="FB｜JGB Smart Property"),
            _camp("3", group="Instagram"),
        ]
        wl = calculate_marketing_workload(campaigns, "Alice")
        assert wl.platform_distribution["FB｜JGB Smart Property"] == 2
        assert wl.platform_distribution["Instagram"] == 1

    def test_content_type_distribution(self):
        campaigns = [
            _camp("1", content_type="Holiday"),
            _camp("2", content_type="Holiday"),
            _camp("3", content_type="Brand Positioning"),
        ]
        wl = calculate_marketing_workload(campaigns, "Alice")
        assert wl.content_type_distribution["Holiday"] == 2

    def test_cross_platform_count(self):
        # Same content name across multiple groups
        campaigns = [
            _camp("1", group="FB｜JGB Smart Property"),
            _camp("2", group="Instagram"),
            _camp("3", group="LinkedIn"),
        ]
        # Override names to be the same base content
        campaigns[0].name = "20260213_馬年賀歲卡"
        campaigns[1].name = "20260213_馬年賀歲卡"
        campaigns[2].name = "unique_post"
        wl = calculate_marketing_workload(campaigns, "Alice")
        assert wl.cross_platform_count == 2  # 2 items share same name

    def test_scheduled_count(self):
        campaigns = [
            _camp("1", status="Completed"),
            _camp("2", status="Scheduled", pub_date="2027-01-01"),
            _camp("3", status="Scheduled", pub_date="2027-02-01"),
        ]
        wl = calculate_marketing_workload(campaigns, "Alice")
        assert wl.scheduled_count == 2

    def test_posts_per_week(self):
        campaigns = [
            _camp("1", pub_date="2026-03-01"),
            _camp("2", pub_date="2026-03-08"),
            _camp("3", pub_date="2026-03-15"),
            _camp("4", pub_date="2026-03-22"),
        ]
        wl = calculate_marketing_workload(campaigns, "Alice")
        # 4 posts over ~3 weeks
        assert wl.posts_per_week > 0

    def test_filters_by_owner(self):
        campaigns = [
            _camp("1", owner="Alice"),
            _camp("2", owner="Bob"),
        ]
        wl = calculate_marketing_workload(campaigns, "Alice")
        assert wl.content_count == 1


import pytest
