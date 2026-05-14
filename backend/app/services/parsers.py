import json
from datetime import date

from app.config.column_mapping import BOARDS, CAMPAIGN_SUBITEM_COLUMNS
from app.models.work_order import WorkOrder
from app.models.campaign import Campaign, CampaignSubitem

WO_COLS = BOARDS["work_orders"]["columns"]
CAMP_COLS = BOARDS["campaigns"]["columns"]


def _get_col(column_values: list[dict], col_id: str) -> dict | None:
    for cv in column_values:
        if cv["id"] == col_id:
            return cv
    return None


def _text_or_default(column_values: list[dict], col_id: str, default: str = "未指定") -> str:
    cv = _get_col(column_values, col_id)
    if cv and cv.get("text") and cv["text"].strip():
        return cv["text"].strip()
    return default


def _parse_date(column_values: list[dict], col_id: str) -> date | None:
    cv = _get_col(column_values, col_id)
    if not cv:
        return None
    text = cv.get("text")
    if text and text.strip():
        try:
            return date.fromisoformat(text.strip())
        except ValueError:
            return None
    return None


def _parse_bool(column_values: list[dict], col_id: str) -> bool:
    cv = _get_col(column_values, col_id)
    if not cv or not cv.get("value"):
        return False
    try:
        val = json.loads(cv["value"])
        return val.get("checked", False)
    except (json.JSONDecodeError, TypeError):
        return False


def parse_work_order(item: dict) -> WorkOrder:
    cols = item.get("column_values", [])
    return WorkOrder(
        id=item["id"],
        name=item["name"],
        client=_text_or_default(cols, WO_COLS["client"]),
        type=_text_or_default(cols, WO_COLS["type"]),
        pm=_text_or_default(cols, WO_COLS["pm"]),
        developer=_text_or_default(cols, WO_COLS["developer"]),
        tester=_text_or_default(cols, WO_COLS["tester"]),
        test_completed_by=_text_or_default(cols, WO_COLS["test_completed_by"]),
        closed_by=_text_or_default(cols, WO_COLS["closed_by"]),
        assign_date=_parse_date(cols, WO_COLS["assign_date"]),
        test_assign_date=_parse_date(cols, WO_COLS["test_assign_date"]),
        test_complete_date=_parse_date(cols, WO_COLS["test_complete_date"]),
        close_date=_parse_date(cols, WO_COLS["close_date"]),
        order_number=_text_or_default(cols, WO_COLS["order_number"], default=""),
    )


def _parse_campaign_subitem(si: dict) -> CampaignSubitem:
    cols = si.get("column_values", [])
    status_col = _get_col(cols, CAMPAIGN_SUBITEM_COLUMNS["status"])
    files_col = _get_col(cols, CAMPAIGN_SUBITEM_COLUMNS["files"])
    has_files = bool(
        files_col
        and files_col.get("text")
        and files_col["text"].strip()
    )
    return CampaignSubitem(
        id=si["id"],
        name=si["name"],
        status=status_col["text"].strip() if status_col and status_col.get("text") and status_col["text"].strip() else "未指定",
        has_files=has_files,
    )


def parse_campaign(item: dict) -> Campaign:
    cols = item.get("column_values", [])
    subitems_raw = item.get("subitems", [])
    group = item.get("group", {})

    subitems = [_parse_campaign_subitem(si) for si in subitems_raw]

    return Campaign(
        id=item["id"],
        name=item["name"],
        owner=_text_or_default(cols, CAMP_COLS["owner"]),
        content_type=_text_or_default(cols, CAMP_COLS["content_type"]),
        publish_date=_parse_date(cols, CAMP_COLS["publish_date"]),
        review_status=_text_or_default(cols, CAMP_COLS["review_status"]),
        completion_status=_text_or_default(cols, CAMP_COLS["completion_status"]),
        platform=_text_or_default(cols, CAMP_COLS["platform"]),
        has_ads=_parse_bool(cols, CAMP_COLS["has_ads"]),
        language=_text_or_default(cols, CAMP_COLS["language"]),
        group_name=group.get("title", "未指定"),
        subitems=subitems,
    )


def filter_templates(campaigns: list[Campaign]) -> list[Campaign]:
    return [c for c in campaigns if not c.is_template]
