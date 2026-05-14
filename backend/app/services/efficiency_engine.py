import math
from collections import defaultdict
from datetime import date, timedelta

from app.models.work_order import WorkOrder
from app.models.campaign import Campaign
from app.models.kpi import (
    EfficiencyMetrics,
    EfficiencyByType,
    AgingOrder,
    WeeklyTrend,
    MarketingEfficiency,
)


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0


def calculate_efficiency(
    orders: list[WorkOrder], today: date | None = None
) -> EfficiencyMetrics:
    if not orders:
        return EfficiencyMetrics()

    today = today or date.today()

    total_days_list = [o.total_days for o in orders if o.total_days is not None]
    dev_days_list = [o.dev_days for o in orders if o.dev_days is not None]
    test_days_list = [o.test_days for o in orders if o.test_days is not None]

    closed = sum(1 for o in orders if o.status == "已結案")
    close_rate = round(closed / len(orders) * 100, 2) if orders else 0

    # Stalled: assigned >7 days ago, no test date, not closed
    stalled = []
    assigned_not_done = [
        o for o in orders
        if o.assign_date and not o.test_assign_date and not o.close_date
    ]
    for o in assigned_not_done:
        days_open = (today - o.assign_date).days  # type: ignore[operator]
        if days_open > 7:
            stalled.append(o.id)

    stalled_rate = round(len(stalled) / len(orders) * 100, 2) if orders else 0

    return EfficiencyMetrics(
        avg_total_days=_safe_avg(total_days_list),
        avg_dev_days=_safe_avg(dev_days_list),
        avg_test_days=_safe_avg(test_days_list),
        close_rate=close_rate,
        stalled_rate=stalled_rate,
        stalled_orders=stalled,
    )


def calculate_efficiency_by_type(orders: list[WorkOrder]) -> list[EfficiencyByType]:
    groups: dict[str, list[WorkOrder]] = defaultdict(list)
    for o in orders:
        groups[o.type].append(o)

    results = []
    for type_name, type_orders in sorted(groups.items()):
        total_days = [o.total_days for o in type_orders if o.total_days is not None]
        dev_days = [o.dev_days for o in type_orders if o.dev_days is not None]
        test_days = [o.test_days for o in type_orders if o.test_days is not None]
        closed = sum(1 for o in type_orders if o.status == "已結案")
        close_rate = round(closed / len(type_orders) * 100, 2) if type_orders else 0

        results.append(EfficiencyByType(
            type_name=type_name,
            count=len(type_orders),
            avg_total_days=_safe_avg(total_days),
            avg_dev_days=_safe_avg(dev_days),
            avg_test_days=_safe_avg(test_days),
            close_rate=close_rate,
        ))
    return results


def find_stalled_orders(
    orders: list[WorkOrder],
    threshold_days: int = 7,
    today: date | None = None,
) -> list[AgingOrder]:
    today = today or date.today()
    stalled = []

    for o in orders:
        if not o.assign_date or o.test_assign_date or o.close_date:
            continue
        days_open = (today - o.assign_date).days
        if days_open <= threshold_days:
            continue

        if days_open <= 3:
            severity = "green"
        elif days_open <= 7:
            severity = "yellow"
        else:
            severity = "red"

        stalled.append(AgingOrder(
            id=o.id,
            name=o.name,
            client=o.client,
            developer=o.developer,
            assign_date=o.assign_date,
            days_open=days_open,
            severity=severity,
        ))

    return sorted(stalled, key=lambda x: x.days_open, reverse=True)


def calculate_weekly_trends(
    orders: list[WorkOrder],
    weeks: int = 12,
    today: date | None = None,
) -> list[WeeklyTrend]:
    today = today or date.today()
    trends = []

    for i in range(weeks - 1, -1, -1):
        # Current week's Monday
        current_monday = today - timedelta(days=today.weekday())
        week_start = current_monday - timedelta(weeks=i)
        week_end_inclusive = week_start + timedelta(days=6)

        week_orders = [
            o for o in orders
            if o.assign_date and week_start <= o.assign_date <= week_end_inclusive
        ]
        closed_in_week = [o for o in week_orders if o.close_date]
        close_rate = round(
            len(closed_in_week) / len(week_orders) * 100, 2
        ) if week_orders else 0

        days_list = [o.total_days for o in closed_in_week if o.total_days is not None]
        avg_days = _safe_avg(days_list)

        bug_count = sum(1 for o in week_orders if o.type == "臭蟲")
        change_count = sum(1 for o in week_orders if o.type == "異動")

        trends.append(WeeklyTrend(
            week_start=week_start.isoformat(),
            week_end=week_end_inclusive.isoformat(),
            task_count=len(week_orders),
            close_rate=close_rate,
            avg_days=avg_days,
            bug_count=bug_count,
            change_count=change_count,
        ))

    return trends


def calculate_marketing_efficiency(campaigns: list[Campaign]) -> MarketingEfficiency:
    if not campaigns:
        return MarketingEfficiency()

    completed = sum(1 for c in campaigns if c.completion_status == "Completed")
    completion_rate = round(completed / len(campaigns) * 100, 2)

    # Weekly std dev
    weekly_counts: dict[str, int] = defaultdict(int)
    for c in campaigns:
        if c.publish_date:
            iso_week = c.publish_date.isocalendar()
            week_key = f"{iso_week[0]}-W{iso_week[1]:02d}"
            weekly_counts[week_key] += 1

    weekly_std_dev = 0.0
    if len(weekly_counts) >= 2:
        counts = list(weekly_counts.values())
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        weekly_std_dev = round(math.sqrt(variance), 2)

    # Material completeness
    completeness_values = [
        c.material_completeness for c in campaigns if c.subitems
    ]
    material_completeness = _safe_avg(completeness_values)

    return MarketingEfficiency(
        completion_rate=completion_rate,
        weekly_std_dev=weekly_std_dev,
        material_completeness=material_completeness,
    )
