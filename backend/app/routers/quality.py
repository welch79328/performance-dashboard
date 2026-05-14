from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.routers.auth import get_current_user
from app.routers.data_deps import get_parsed_data_from_db
from app.services.quality_engine import (
    calculate_bug_recurrence,
    calculate_change_density,
)

router = APIRouter(prefix="/api/quality", tags=["quality"])


@router.get("/overview")
async def quality_overview(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return calculate_change_density(data["work_orders"])


@router.get("/bug-recurrence")
async def bug_recurrence(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return calculate_bug_recurrence(data["work_orders"])
