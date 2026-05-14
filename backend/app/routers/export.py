from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.routers.auth import get_current_user
from app.routers.data_deps import get_monday_service, get_parsed_data
from app.services.workload_engine import calculate_team_workload
from app.services.efficiency_engine import (
    calculate_efficiency,
    calculate_efficiency_by_type,
    calculate_weekly_trends,
)
from app.services.schedule_engine import generate_aging_table
from app.services.export_service import generate_weekly_report, generate_monthly_report

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/weekly")
async def export_weekly(
    current_user: dict = Depends(get_current_user),
):
    svc = get_monday_service()
    data = await get_parsed_data(svc)
    orders = data["work_orders"]

    team_kpi = calculate_team_workload(orders)
    efficiency = calculate_efficiency(orders)
    by_type = calculate_efficiency_by_type(orders)
    aging = generate_aging_table(orders)

    today = date.today()
    week_start = today - __import__("datetime").timedelta(days=today.weekday())
    week_end = week_start + __import__("datetime").timedelta(days=6)
    label = f"{week_start.isoformat()} ~ {week_end.isoformat()}"

    buf = generate_weekly_report(
        team_kpi=team_kpi, orders=orders,
        efficiency=efficiency, efficiency_by_type=by_type,
        aging_orders=aging, date_range_label=label,
    )

    return Response(
        content=buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="weekly_report_{today.isoformat()}.xlsx"'},
    )


@router.get("/monthly")
async def export_monthly(
    current_user: dict = Depends(get_current_user),
):
    svc = get_monday_service()
    data = await get_parsed_data(svc)
    orders = data["work_orders"]

    team_kpi = calculate_team_workload(orders)
    efficiency = calculate_efficiency(orders)
    by_type = calculate_efficiency_by_type(orders)
    aging = generate_aging_table(orders)
    trends = calculate_weekly_trends(orders, weeks=12)

    today = date.today()
    label = f"{today.year}-{today.month:02d}"

    buf = generate_monthly_report(
        team_kpi=team_kpi, orders=orders,
        efficiency=efficiency, efficiency_by_type=by_type,
        aging_orders=aging, trends=trends,
        date_range_label=label,
    )

    return Response(
        content=buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="monthly_report_{label}.xlsx"'},
    )
