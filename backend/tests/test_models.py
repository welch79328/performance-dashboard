from datetime import date

from app.models.work_order import WorkOrder
from app.models.campaign import Campaign, CampaignSubitem
from app.models.monday import MondayColumnValue, MondayItem, MondayUser
from app.models.kpi import (
    PersonWorkload,
    MarketingWorkload,
    EfficiencyMetrics,
    EfficiencyByType,
    GanttItem,
    HeatmapCell,
    AgingOrder,
    QualityMetrics,
    TeamKPI,
    WeeklyTrend,
    DateRangeRequest,
    MarketingEfficiency,
)


# === WorkOrder computed fields ===

class TestWorkOrderStatus:
    def test_status_closed(self):
        wo = WorkOrder(
            id="1", name="test",
            assign_date=date(2026, 5, 1),
            test_assign_date=date(2026, 5, 3),
            close_date=date(2026, 5, 5),
        )
        assert wo.status == "已結案"

    def test_status_testing(self):
        wo = WorkOrder(
            id="1", name="test",
            assign_date=date(2026, 5, 1),
            test_assign_date=date(2026, 5, 3),
        )
        assert wo.status == "測試中"

    def test_status_developing(self):
        wo = WorkOrder(
            id="1", name="test",
            assign_date=date(2026, 5, 1),
        )
        assert wo.status == "開發中"

    def test_status_unassigned(self):
        wo = WorkOrder(id="1", name="test")
        assert wo.status == "未指派"

    def test_total_days(self):
        wo = WorkOrder(
            id="1", name="test",
            assign_date=date(2026, 5, 1),
            close_date=date(2026, 5, 8),
        )
        assert wo.total_days == 7

    def test_total_days_none_when_not_closed(self):
        wo = WorkOrder(id="1", name="test", assign_date=date(2026, 5, 1))
        assert wo.total_days is None

    def test_dev_days(self):
        wo = WorkOrder(
            id="1", name="test",
            assign_date=date(2026, 5, 1),
            test_assign_date=date(2026, 5, 4),
        )
        assert wo.dev_days == 3

    def test_test_days(self):
        wo = WorkOrder(
            id="1", name="test",
            test_assign_date=date(2026, 5, 4),
            close_date=date(2026, 5, 5),
        )
        assert wo.test_days == 1

    def test_same_day_completion(self):
        wo = WorkOrder(
            id="1", name="test",
            assign_date=date(2026, 5, 1),
            test_assign_date=date(2026, 5, 1),
            close_date=date(2026, 5, 1),
        )
        assert wo.total_days == 0
        assert wo.dev_days == 0
        assert wo.test_days == 0

    def test_defaults(self):
        wo = WorkOrder(id="1", name="test")
        assert wo.client == "未指定"
        assert wo.developer == "未指定"
        assert wo.tester == "未指定"
        assert wo.order_number == ""


# === Campaign computed fields ===

class TestCampaignSubitem:
    def test_copywriting_english(self):
        si = CampaignSubitem(id="1", name="Copywriting")
        assert si.subitem_type == "copywriting"

    def test_copywriting_chinese(self):
        si = CampaignSubitem(id="1", name="文案")
        assert si.subitem_type == "copywriting"

    def test_copywrite_typo(self):
        si = CampaignSubitem(id="1", name="Copywrite")
        assert si.subitem_type == "copywriting"

    def test_visual_english(self):
        si = CampaignSubitem(id="1", name="Visual")
        assert si.subitem_type == "visual"

    def test_visual_chinese(self):
        si = CampaignSubitem(id="1", name="視覺")
        assert si.subitem_type == "visual"

    def test_content_chinese(self):
        si = CampaignSubitem(id="1", name="內容")
        assert si.subitem_type == "visual"

    def test_unknown_type(self):
        si = CampaignSubitem(id="1", name="Something else")
        assert si.subitem_type == "other"


class TestCampaign:
    def test_is_template_true(self):
        c = Campaign(
            id="1", name="template",
            review_status="Cancelled",
            completion_status="Paused",
        )
        assert c.is_template is True

    def test_is_template_false(self):
        c = Campaign(
            id="1", name="real post",
            review_status="Direct-Go",
            completion_status="Completed",
        )
        assert c.is_template is False

    def test_material_completeness_all_done(self):
        c = Campaign(
            id="1", name="test",
            subitems=[
                CampaignSubitem(id="s1", name="Copywriting", status="Done"),
                CampaignSubitem(id="s2", name="Visual", status="Done"),
            ],
        )
        assert c.material_completeness == 100.0

    def test_material_completeness_half(self):
        c = Campaign(
            id="1", name="test",
            subitems=[
                CampaignSubitem(id="s1", name="Copywriting", status="Done"),
                CampaignSubitem(id="s2", name="Visual", status="未指定"),
            ],
        )
        assert c.material_completeness == 50.0

    def test_material_completeness_no_subitems(self):
        c = Campaign(id="1", name="test")
        assert c.material_completeness == 0

    def test_defaults(self):
        c = Campaign(id="1", name="test")
        assert c.owner == "未指定"
        assert c.has_ads is False
        assert c.group_name == "未指定"


# === Monday.com raw models ===

class TestMondayModels:
    def test_column_value(self):
        cv = MondayColumnValue(id="col1", text="hello", value='{"index":1}')
        assert cv.id == "col1"
        assert cv.text == "hello"

    def test_item_with_subitems(self):
        item = MondayItem(
            id="1", name="test",
            column_values=[MondayColumnValue(id="c1", text="v1", value=None)],
            subitems=[],
        )
        assert len(item.column_values) == 1
        assert item.subitems == []

    def test_user(self):
        user = MondayUser(id="123", name="Lenny", email="lenny@test.com")
        assert user.name == "Lenny"


# === KPI models basic instantiation ===

class TestKPIModels:
    def test_person_workload(self):
        pw = PersonWorkload(user_name="Lenny", pm_count=5, dev_count=10, test_count=3, total_count=18)
        assert pw.total_count == 18

    def test_marketing_workload(self):
        mw = MarketingWorkload(
            user_name="Alice",
            content_count=50,
            platform_distribution={"FB": 27, "IG": 16},
        )
        assert mw.platform_distribution["FB"] == 27

    def test_efficiency_metrics(self):
        em = EfficiencyMetrics(avg_total_days=2.2, close_rate=63.0, stalled_rate=5.0)
        assert em.avg_total_days == 2.2

    def test_gantt_item(self):
        gi = GanttItem(
            id="1", name="test", client="JGB", developer="Lenny",
            start_date=date(2026, 5, 1), end_date=None, status="開發中",
        )
        assert gi.end_date is None

    def test_aging_order(self):
        ao = AgingOrder(
            id="1", name="test", client="JGB", developer="Lenny",
            assign_date=date(2026, 5, 1), days_open=10, severity="red",
        )
        assert ao.severity == "red"

    def test_team_kpi(self):
        tk = TeamKPI(department="pm_rd", total_tasks=100, close_rate=63.0)
        assert tk.department == "pm_rd"

    def test_date_range_request(self):
        dr = DateRangeRequest(preset="this-month", department="marketing")
        assert dr.department == "marketing"

    def test_weekly_trend(self):
        wt = WeeklyTrend(week_start="2026-05-05", week_end="2026-05-11", task_count=15)
        assert wt.task_count == 15


# === Column mapping ===

class TestColumnMapping:
    def test_work_orders_board_config(self):
        from app.config.column_mapping import BOARDS
        wo = BOARDS["work_orders"]
        assert wo["board_id"] == "7960591450"
        assert wo["columns"]["client"] == "dropdown_mkkzznt3"
        assert wo["columns"]["developer"] == "color_mkxfagvd"
        assert wo["columns"]["tester"] == "color_mkxfdhzv"
        assert wo["columns"]["closed_by"] == "color_mkxfvdj3"

    def test_campaigns_board_config(self):
        from app.config.column_mapping import BOARDS
        camp = BOARDS["campaigns"]
        assert camp["board_id"] == "18398984308"
        assert camp["columns"]["content_type"] == "color_mm0dy0by"
        assert camp["columns"]["completion_status"] == "color_mm0gy6kv"

    def test_no_launch_plan(self):
        from app.config.column_mapping import BOARDS
        assert "launch_plan" not in BOARDS

    def test_campaign_subitem_columns(self):
        from app.config.column_mapping import CAMPAIGN_SUBITEM_COLUMNS
        assert "status" in CAMPAIGN_SUBITEM_COLUMNS
