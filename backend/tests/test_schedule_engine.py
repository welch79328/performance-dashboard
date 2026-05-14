from datetime import date

import pytest

from app.models.work_order import WorkOrder
from app.services.schedule_engine import (
    generate_gantt,
    generate_heatmap,
    generate_aging_table,
)


def _wo(id: str, dev: str = "Lenny", client: str = "JGB",
        assign: str | None = "2026-05-01", close: str | None = None,
        test_date: str | None = None) -> WorkOrder:
    return WorkOrder(
        id=id, name=f"WO-{id}", developer=dev, client=client,
        assign_date=date.fromisoformat(assign) if assign else None,
        test_assign_date=date.fromisoformat(test_date) if test_date else None,
        close_date=date.fromisoformat(close) if close else None,
    )


# === Gantt chart data ===

class TestGenerateGantt:
    def test_closed_order(self):
        orders = [_wo("1", assign="2026-05-01", close="2026-05-05")]
        gantt = generate_gantt(orders)
        assert len(gantt) == 1
        assert gantt[0].start_date == date(2026, 5, 1)
        assert gantt[0].end_date == date(2026, 5, 5)
        assert gantt[0].status == "已結案"

    def test_in_progress_order_end_date_none(self):
        orders = [_wo("1", assign="2026-05-01")]
        gantt = generate_gantt(orders)
        assert gantt[0].end_date is None
        assert gantt[0].status == "開發中"

    def test_no_assign_date_excluded(self):
        orders = [_wo("1", assign=None)]
        gantt = generate_gantt(orders)
        assert len(gantt) == 0

    def test_includes_developer_and_client(self):
        orders = [_wo("1", dev="Abu", client="富喬", assign="2026-05-01")]
        gantt = generate_gantt(orders)
        assert gantt[0].developer == "Abu"
        assert gantt[0].client == "富喬"

    def test_multiple_orders_sorted_by_start(self):
        orders = [
            _wo("2", assign="2026-05-10"),
            _wo("1", assign="2026-05-01"),
            _wo("3", assign="2026-05-05"),
        ]
        gantt = generate_gantt(orders)
        assert gantt[0].id == "1"
        assert gantt[1].id == "3"
        assert gantt[2].id == "2"


# === Heatmap ===

class TestGenerateHeatmap:
    def test_person_dimension(self):
        orders = [
            _wo("1", dev="Lenny", assign="2026-05-05"),
            _wo("2", dev="Lenny", assign="2026-05-06"),
            _wo("3", dev="Abu", assign="2026-05-05"),
        ]
        heatmap = generate_heatmap(orders, dimension="person")
        # Find Lenny's cell for week of 5/5
        lenny_cells = [c for c in heatmap if c.label == "Lenny"]
        assert any(c.count == 2 for c in lenny_cells)

    def test_client_dimension(self):
        orders = [
            _wo("1", client="JGB", assign="2026-05-05"),
            _wo("2", client="JGB", assign="2026-05-06"),
            _wo("3", client="富喬", assign="2026-05-05"),
        ]
        heatmap = generate_heatmap(orders, dimension="client")
        jgb_cells = [c for c in heatmap if c.label == "JGB"]
        assert any(c.count == 2 for c in jgb_cells)

    def test_week_format(self):
        orders = [_wo("1", assign="2026-05-05")]
        heatmap = generate_heatmap(orders, dimension="person")
        assert heatmap[0].week.startswith("2026-W")

    def test_empty_orders(self):
        heatmap = generate_heatmap([], dimension="person")
        assert len(heatmap) == 0


# === Aging table ===

class TestGenerateAgingTable:
    def test_only_open_orders(self):
        orders = [
            _wo("1", assign="2026-05-01", close="2026-05-03"),  # closed
            _wo("2", assign="2026-05-01"),                       # open
        ]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert len(aging) == 1
        assert aging[0].id == "2"

    def test_days_open_calculation(self):
        orders = [_wo("1", assign="2026-05-01")]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert aging[0].days_open == 9

    def test_severity_green(self):
        orders = [_wo("1", assign="2026-05-08")]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert aging[0].severity == "green"

    def test_severity_yellow(self):
        orders = [_wo("1", assign="2026-05-05")]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert aging[0].severity == "yellow"

    def test_severity_red(self):
        orders = [_wo("1", assign="2026-04-25")]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert aging[0].severity == "red"

    def test_sorted_by_days_open_desc(self):
        orders = [
            _wo("1", assign="2026-05-08"),  # 2 days
            _wo("2", assign="2026-05-01"),  # 9 days
            _wo("3", assign="2026-05-05"),  # 5 days
        ]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert aging[0].days_open > aging[1].days_open > aging[2].days_open

    def test_no_assign_date_excluded(self):
        orders = [_wo("1", assign=None)]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert len(aging) == 0

    def test_testing_orders_included(self):
        orders = [_wo("1", assign="2026-05-01", test_date="2026-05-03")]
        aging = generate_aging_table(orders, today=date(2026, 5, 10))
        assert len(aging) == 1  # still open (no close_date)
