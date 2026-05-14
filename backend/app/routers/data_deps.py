from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.engine import get_session
from app.services.monday_api import MondayAPIService
from app.services.sync_service import get_work_orders_from_db, get_campaigns_from_db


_monday_service: MondayAPIService | None = None


def get_monday_service() -> MondayAPIService:
    global _monday_service
    if _monday_service is None:
        _monday_service = MondayAPIService(
            api_token=settings.monday_api_token,
            cache_ttl=settings.cache_ttl_seconds,
        )
    return _monday_service


def set_monday_service(service: MondayAPIService | None) -> None:
    global _monday_service
    _monday_service = service


async def get_parsed_data_from_db(session: AsyncSession) -> dict:
    """Read pre-synced data from PostgreSQL."""
    work_orders = await get_work_orders_from_db(session)
    campaigns = await get_campaigns_from_db(session)
    return {
        "work_orders": work_orders,
        "campaigns": campaigns,
    }


async def get_parsed_data(service: MondayAPIService | None = None) -> dict:
    """Fallback: fetch from Monday.com API directly (used when DB is empty or in tests)."""
    from app.services.parsers import parse_work_order, parse_campaign, filter_templates

    svc = service or get_monday_service()
    raw = await svc.sync_all()

    work_orders = [parse_work_order(item) for item in raw["work_orders"]]
    campaigns_all = [parse_campaign(item) for item in raw["campaigns"]]
    campaigns = filter_templates(campaigns_all)
    users = raw["users"]

    return {
        "work_orders": work_orders,
        "campaigns": campaigns,
        "users": users,
    }
