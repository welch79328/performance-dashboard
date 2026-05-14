from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.routers.auth import get_current_user
from app.routers.data_deps import get_parsed_data_from_db
from app.services.workload_engine import (
    calculate_person_workload,
    calculate_team_workload,
    calculate_marketing_workload,
    filter_by_date_range,
)

router = APIRouter(prefix="/api/workload", tags=["workload"])


@router.get("/team")
async def team_workload(
    department: str = Query("pm_rd"),
    start: date | None = Query(None),
    end: date | None = Query(None),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)

    if department == "marketing":
        from collections import Counter
        from app.services.efficiency_engine import calculate_marketing_efficiency
        from app.services.workload_engine import calculate_marketing_workload
        campaigns = data["campaigns"]
        me = calculate_marketing_efficiency(campaigns)

        # Collect unique owners
        owners = sorted(set(c.owner for c in campaigns if c.owner != "未指定"))
        member_workloads = [calculate_marketing_workload(campaigns, name) for name in owners]

        # Platform & content type distribution
        platform_dist = dict(Counter(c.group_name for c in campaigns))
        content_dist = dict(Counter(c.content_type for c in campaigns))

        return {
            "department": "marketing",
            "total_tasks": len(campaigns),
            "completed_tasks": sum(1 for c in campaigns if c.completion_status == "Completed"),
            "in_progress_tasks": sum(1 for c in campaigns if c.completion_status != "Completed"),
            "close_rate": me.completion_rate,
            "avg_processing_days": 0,
            "member_workloads": [mw.model_dump() for mw in member_workloads],
            "type_distribution": content_dist,
            "client_distribution": platform_dist,
        }

    orders = data["work_orders"]
    if start and end:
        orders = filter_by_date_range(orders, start, end)

    # Get active team member names from DB to filter out departed members
    from app.services.user_service import get_all_users
    db_users = await get_all_users(session)
    active_names = {u.name for u in db_users}
    # Also match by first name (Monday.com uses "Lenny", DB has "Lenny Chen")
    active_first_names = {u.name.split()[0] for u in db_users}
    active_members = active_names | active_first_names

    team = calculate_team_workload(orders, active_members=active_members)
    return team


@router.get("/member/{name}")
async def member_workload(
    name: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from app.services.user_service import get_all_users
    from app.services.workload_engine import calculate_marketing_workload

    data = await get_parsed_data_from_db(session)

    # Check if this person is marketing
    db_users = await get_all_users(session)
    user_record = next((u for u in db_users if u.name == name or u.name.split()[0] == name.split()[0]), None)
    is_marketing = user_record and user_record.department == "marketing"

    if is_marketing:
        campaigns = data["campaigns"]
        matched_name = _find_matching_name_in_campaigns(campaigns, name)
        mw = calculate_marketing_workload(campaigns, matched_name)
        member_campaigns = [c for c in campaigns if c.owner == matched_name]
        return {
            "department": "marketing",
            "workload": mw.model_dump(),
            "orders": [c.model_dump() for c in member_campaigns],
        }

    orders = data["work_orders"]
    matched_name = _find_matching_name(orders, name)
    workload = calculate_person_workload(orders, matched_name)
    member_orders = [
        o for o in orders
        if o.pm == matched_name or o.developer == matched_name or o.tester == matched_name
    ]
    return {
        "department": "pm_rd",
        "workload": workload,
        "orders": member_orders,
    }


def _find_matching_name(orders: list, query: str) -> str:
    """Find the Monday.com name that best matches the query."""
    query_lower = query.lower()
    # Collect all unique names
    names: set[str] = set()
    for o in orders:
        for field in [o.pm, o.developer, o.tester]:
            if field and field != "未指定":
                names.add(field)

    # Exact match first
    for n in names:
        if n.lower() == query_lower:
            return n

    # Partial match (query contains name or name contains query)
    for n in names:
        if query_lower in n.lower() or n.lower() in query_lower:
            return n

    # First name match (e.g., "Lenny Chen" → "Lenny")
    query_first = query_lower.split()[0] if query_lower else ""
    for n in names:
        if n.lower().split()[0] == query_first:
            return n

    return query  # fallback to original


def _find_matching_name_in_campaigns(campaigns: list, query: str) -> str:
    """Find the campaign owner name that best matches the query."""
    query_lower = query.lower()
    names = set(c.owner for c in campaigns if c.owner != "未指定")

    for n in names:
        if n.lower() == query_lower:
            return n
    for n in names:
        if query_lower in n.lower() or n.lower() in query_lower:
            return n
    query_first = query_lower.split()[0] if query_lower else ""
    for n in names:
        if n.lower().split()[0] == query_first:
            return n
    return query
