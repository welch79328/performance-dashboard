import logging
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import WorkOrderRecord, CampaignRecord, SyncLog
from app.services.monday_api import MondayAPIService
from app.services.parsers import parse_work_order, parse_campaign, filter_templates

logger = logging.getLogger(__name__)


async def sync_monday_to_db(session: AsyncSession, monday_service: MondayAPIService) -> dict:
    """Sync Monday.com data into PostgreSQL. Returns sync summary."""
    results = {"work_orders": 0, "campaigns": 0, "errors": []}

    try:
        raw = await monday_service.sync_all()
    except Exception as e:
        logger.error(f"Monday.com sync failed: {e}")
        await _log_sync(session, "all", 0, "failed", str(e))
        raise

    # Sync work orders
    try:
        work_orders = [parse_work_order(item) for item in raw["work_orders"]]
        await _upsert_work_orders(session, work_orders)
        results["work_orders"] = len(work_orders)
        await _log_sync(session, "work_orders", len(work_orders), "success")
    except Exception as e:
        logger.error(f"Work order sync failed: {e}")
        results["errors"].append(f"work_orders: {e}")
        await _log_sync(session, "work_orders", 0, "failed", str(e))

    # Sync campaigns
    try:
        campaigns_all = [parse_campaign(item) for item in raw["campaigns"]]
        campaigns = filter_templates(campaigns_all)
        await _upsert_campaigns(session, campaigns)
        results["campaigns"] = len(campaigns)
        await _log_sync(session, "campaigns", len(campaigns), "success")
    except Exception as e:
        logger.error(f"Campaign sync failed: {e}")
        results["errors"].append(f"campaigns: {e}")
        await _log_sync(session, "campaigns", 0, "failed", str(e))

    await session.commit()
    return results


async def _upsert_work_orders(session: AsyncSession, work_orders: list) -> None:
    existing = {}
    result = await session.execute(select(WorkOrderRecord))
    for row in result.scalars().all():
        existing[row.monday_id] = row

    for wo in work_orders:
        if wo.id in existing:
            record = existing[wo.id]
        else:
            record = WorkOrderRecord(monday_id=wo.id)
            session.add(record)

        record.name = wo.name
        record.client = wo.client
        record.type = wo.type
        record.pm = wo.pm
        record.developer = wo.developer
        record.tester = wo.tester
        record.test_completed_by = wo.test_completed_by
        record.closed_by = wo.closed_by
        record.assign_date = wo.assign_date
        record.test_assign_date = wo.test_assign_date
        record.test_complete_date = wo.test_complete_date
        record.close_date = wo.close_date
        record.order_number = wo.order_number


async def _upsert_campaigns(session: AsyncSession, campaigns: list) -> None:
    existing = {}
    result = await session.execute(select(CampaignRecord))
    for row in result.scalars().all():
        existing[row.monday_id] = row

    for c in campaigns:
        if c.id in existing:
            record = existing[c.id]
        else:
            record = CampaignRecord(monday_id=c.id)
            session.add(record)

        record.name = c.name
        record.owner = c.owner
        record.content_type = c.content_type
        record.publish_date = c.publish_date
        record.review_status = c.review_status
        record.completion_status = c.completion_status
        record.platform = c.platform
        record.has_ads = c.has_ads
        record.language = c.language
        record.group_name = c.group_name
        record.is_template = c.is_template
        record.material_completeness = c.material_completeness


async def _log_sync(
    session: AsyncSession, board: str, count: int, status: str, error: str | None = None
) -> None:
    session.add(SyncLog(
        board_name=board,
        items_count=count,
        status=status,
        error_message=error,
    ))


async def get_work_orders_from_db(session: AsyncSession) -> list:
    """Read work orders from DB and convert to WorkOrder models."""
    from app.models.work_order import WorkOrder

    result = await session.execute(select(WorkOrderRecord))
    records = result.scalars().all()
    return [
        WorkOrder(
            id=r.monday_id,
            name=r.name,
            client=r.client,
            type=r.type,
            pm=r.pm,
            developer=r.developer,
            tester=r.tester,
            test_completed_by=r.test_completed_by,
            closed_by=r.closed_by,
            assign_date=r.assign_date,
            test_assign_date=r.test_assign_date,
            test_complete_date=r.test_complete_date,
            close_date=r.close_date,
            order_number=r.order_number,
        )
        for r in records
    ]


async def get_campaigns_from_db(session: AsyncSession) -> list:
    """Read campaigns from DB and convert to Campaign models."""
    from app.models.campaign import Campaign

    result = await session.execute(select(CampaignRecord).where(CampaignRecord.is_template == False))
    records = result.scalars().all()
    return [
        Campaign(
            id=r.monday_id,
            name=r.name,
            owner=r.owner,
            content_type=r.content_type,
            publish_date=r.publish_date,
            review_status=r.review_status,
            completion_status=r.completion_status,
            platform=r.platform,
            has_ads=r.has_ads,
            language=r.language,
            group_name=r.group_name,
        )
        for r in records
    ]


async def get_last_sync_time(session: AsyncSession) -> str | None:
    result = await session.execute(
        select(SyncLog.synced_at)
        .where(SyncLog.status == "success")
        .order_by(SyncLog.synced_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row.isoformat() if row else None
