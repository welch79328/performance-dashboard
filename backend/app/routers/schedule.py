from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.routers.auth import get_current_user
from app.routers.data_deps import get_parsed_data_from_db
from app.services.schedule_engine import (
    generate_gantt,
    generate_heatmap,
    generate_aging_table,
)

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.get("/gantt")
async def gantt(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return generate_gantt(data["work_orders"])


@router.get("/heatmap/person")
async def heatmap_person(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return generate_heatmap(data["work_orders"], dimension="person")


@router.get("/heatmap/client")
async def heatmap_client(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return generate_heatmap(data["work_orders"], dimension="client")


@router.get("/aging")
async def aging_table(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return generate_aging_table(data["work_orders"])


@router.get("/calendar")
async def marketing_calendar(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await get_parsed_data_from_db(session)
    return data["campaigns"]
