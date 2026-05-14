from collections import defaultdict
from datetime import date

from app.models.work_order import WorkOrder
from app.models.kpi import GanttItem, HeatmapCell, AgingOrder


def generate_gantt(orders: list[WorkOrder]) -> list[GanttItem]:
    items = []
    for o in orders:
        if not o.assign_date:
            continue
        items.append(GanttItem(
            id=o.id,
            name=o.name,
            client=o.client,
            developer=o.developer,
            start_date=o.assign_date,
            end_date=o.close_date,
            status=o.status,
        ))
    return sorted(items, key=lambda x: x.start_date)


def generate_heatmap(
    orders: list[WorkOrder], dimension: str = "person"
) -> list[HeatmapCell]:
    counts: dict[tuple[str, str], int] = defaultdict(int)

    for o in orders:
        if not o.assign_date:
            continue
        iso = o.assign_date.isocalendar()
        week = f"{iso[0]}-W{iso[1]:02d}"

        if dimension == "person":
            label = o.developer
        else:
            label = o.client

        counts[(label, week)] += 1

    return [
        HeatmapCell(label=label, week=week, count=count)
        for (label, week), count in sorted(counts.items())
    ]


def generate_aging_table(
    orders: list[WorkOrder], today: date | None = None
) -> list[AgingOrder]:
    today = today or date.today()
    aging = []

    for o in orders:
        if not o.assign_date or o.close_date:
            continue

        days_open = (today - o.assign_date).days

        if days_open <= 3:
            severity = "green"
        elif days_open <= 7:
            severity = "yellow"
        else:
            severity = "red"

        aging.append(AgingOrder(
            id=o.id,
            name=o.name,
            client=o.client,
            developer=o.developer,
            assign_date=o.assign_date,
            days_open=days_open,
            severity=severity,
        ))

    return sorted(aging, key=lambda x: x.days_open, reverse=True)
