from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.routers.auth import get_current_user
from app.routers.data_deps import get_monday_service
from app.services.sync_service import sync_monday_to_db, get_last_sync_time
from app.services.user_service import get_all_users

router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync")
async def trigger_sync(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    svc = get_monday_service()
    svc.clear_cache()
    result = await sync_monday_to_db(session, svc)
    last_time = await get_last_sync_time(session)
    return {
        "last_sync_time": last_time,
        "work_orders_synced": result["work_orders"],
        "campaigns_synced": result["campaigns"],
        "errors": result["errors"],
    }


@router.get("/sync/status")
async def sync_status(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    last_time = await get_last_sync_time(session)
    return {"last_sync_time": last_time}


@router.get("/users")
async def list_users(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    users = await get_all_users(session)
    return [
        {"id": u.monday_user_id, "name": u.name, "email": u.email, "department": u.department}
        for u in users
    ]
