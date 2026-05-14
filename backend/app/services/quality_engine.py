from collections import Counter, defaultdict
from datetime import date, timedelta

from app.models.work_order import WorkOrder
from app.models.campaign import Campaign
from app.models.kpi import QualityMetrics


def calculate_bug_recurrence(orders: list[WorkOrder]) -> dict[str, int]:
    bugs = [o for o in orders if o.type == "臭蟲"]
    counts = Counter(o.client for o in bugs)
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def calculate_change_density(
    orders: list[WorkOrder],
    weeks: int = 12,
    today: date | None = None,
) -> QualityMetrics:
    today = today or date.today()

    total = len(orders)
    changes = sum(1 for o in orders if o.type == "異動")
    density = round(changes / total * 100, 2) if total > 0 else 0

    # Weekly trend
    trend: list[float] = []
    for i in range(weeks - 1, -1, -1):
        current_monday = today - timedelta(days=today.weekday())
        week_start = current_monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)

        week_orders = [
            o for o in orders
            if o.assign_date and week_start <= o.assign_date <= week_end
        ]
        week_changes = sum(1 for o in week_orders if o.type == "異動")
        week_density = round(
            week_changes / len(week_orders) * 100, 2
        ) if week_orders else 0
        trend.append(week_density)

    bug_recurrence = calculate_bug_recurrence(orders)

    return QualityMetrics(
        bug_recurrence=bug_recurrence,
        change_density=density,
        change_density_trend=trend,
    )


def calculate_material_completeness_avg(campaigns: list[Campaign]) -> float:
    values = [c.material_completeness for c in campaigns if c.subitems]
    if not values:
        return 0
    return round(sum(values) / len(values), 2)
