from collections import Counter
from datetime import date

from app.models.work_order import WorkOrder
from app.models.campaign import Campaign
from app.models.kpi import PersonWorkload, MarketingWorkload, TeamKPI


def filter_by_date_range(
    orders: list[WorkOrder], start: date, end: date
) -> list[WorkOrder]:
    return [
        o for o in orders
        if o.assign_date and start <= o.assign_date <= end
    ]


def calculate_person_workload(
    orders: list[WorkOrder], person_name: str
) -> PersonWorkload:
    pm_count = 0
    dev_count = 0
    test_count = 0
    unique_ids: set[str] = set()
    in_progress_ids: set[str] = set()

    for o in orders:
        is_related = False
        if o.pm == person_name:
            pm_count += 1
            is_related = True
        if o.developer == person_name:
            dev_count += 1
            is_related = True
        if o.tester == person_name:
            test_count += 1
            is_related = True

        if is_related:
            unique_ids.add(o.id)
            if o.status != "已結案":
                in_progress_ids.add(o.id)

    return PersonWorkload(
        user_name=person_name,
        unique_count=len(unique_ids),
        pm_count=pm_count,
        dev_count=dev_count,
        test_count=test_count,
        total_count=pm_count + dev_count + test_count,
        in_progress_count=len(in_progress_ids),
    )


def calculate_team_workload(orders: list[WorkOrder], active_members: set[str] | None = None) -> TeamKPI:
    total = len(orders)
    completed = sum(1 for o in orders if o.status == "已結案")
    in_progress = total - completed
    close_rate = (completed / total * 100) if total > 0 else 0

    avg_days = 0.0
    days_list = [o.total_days for o in orders if o.total_days is not None]
    if days_list:
        avg_days = sum(days_list) / len(days_list)

    # Collect all unique person names across PM/dev/test roles
    person_names: set[str] = set()
    for o in orders:
        if o.pm and o.pm != "未指定":
            person_names.add(o.pm)
        if o.developer and o.developer != "未指定":
            person_names.add(o.developer)
        if o.tester and o.tester != "未指定":
            person_names.add(o.tester)

    # Filter to active team members only
    if active_members:
        person_names = {n for n in person_names if n in active_members}

    member_workloads = [
        calculate_person_workload(orders, name)
        for name in sorted(person_names)
    ]

    return TeamKPI(
        department="pm_rd",
        total_tasks=total,
        completed_tasks=completed,
        in_progress_tasks=in_progress,
        close_rate=round(close_rate, 2),
        avg_processing_days=round(avg_days, 2),
        member_workloads=member_workloads,
        type_distribution=calculate_type_distribution(orders),
        client_distribution=calculate_client_distribution(orders),
    )


def calculate_client_distribution(orders: list[WorkOrder]) -> dict[str, int]:
    return dict(Counter(o.client for o in orders))


def calculate_type_distribution(orders: list[WorkOrder]) -> dict[str, int]:
    return dict(Counter(o.type for o in orders))


def calculate_marketing_workload(
    campaigns: list[Campaign], person_name: str
) -> MarketingWorkload:
    owned = [c for c in campaigns if c.owner == person_name]

    platform_dist = dict(Counter(c.group_name for c in owned))
    content_type_dist = dict(Counter(c.content_type for c in owned))

    # Cross-platform: count items whose name appears more than once across different groups
    name_groups: dict[str, set[str]] = {}
    for c in owned:
        name_groups.setdefault(c.name, set()).add(c.group_name)
    cross_platform = sum(
        len(groups) for name, groups in name_groups.items() if len(groups) > 1
    )

    scheduled = sum(1 for c in owned if c.completion_status == "Scheduled")

    # Posts per week
    posts_per_week = 0.0
    dates = sorted([c.publish_date for c in owned if c.publish_date])
    if len(dates) >= 2:
        span_days = (dates[-1] - dates[0]).days
        weeks = max(span_days / 7, 1)
        posts_per_week = round(len(dates) / weeks, 1)
    elif len(dates) == 1:
        posts_per_week = 1.0

    return MarketingWorkload(
        user_name=person_name,
        content_count=len(owned),
        platform_distribution=platform_dist,
        content_type_distribution=content_type_dist,
        cross_platform_count=cross_platform,
        scheduled_count=scheduled,
        posts_per_week=posts_per_week,
    )
