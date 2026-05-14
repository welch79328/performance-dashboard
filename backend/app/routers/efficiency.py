from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.routers.auth import get_current_user
from app.routers.data_deps import get_parsed_data_from_db
from app.services.efficiency_engine import (
    calculate_efficiency,
    calculate_efficiency_by_type,
    find_stalled_orders,
    calculate_weekly_trends,
)

router = APIRouter(prefix="/api/efficiency", tags=["efficiency"])


@router.get("/overview")
async def efficiency_overview(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    orders = data["work_orders"]
    return {
        "efficiency": calculate_efficiency(orders),
        "by_type": calculate_efficiency_by_type(orders),
    }


@router.get("/stalled")
async def stalled_orders(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return find_stalled_orders(data["work_orders"])


@router.get("/trends")
async def efficiency_trends(
    weeks: int = 12,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return calculate_weekly_trends(data["work_orders"], weeks=weeks)
