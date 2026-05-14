from datetime import date

from app.services.parsers import parse_work_order, parse_campaign, filter_templates


# === Work Order parsing ===

def _make_wo_item(overrides: dict | None = None) -> dict:
    """Helper to build a realistic Monday.com work order item."""
    base = {
        "id": "12345",
        "name": "[開發]帳單品項新增狀態",
        "column_values": [
            {"id": "dropdown_mkkzznt3", "text": "JGB, 資育", "value": '{"ids":[3,49]}', "type": "dropdown"},
            {"id": "color_mkxfd8jn", "text": "開發", "value": '{"index":4}', "type": "status"},
            {"id": "color_mkxfxqs2", "text": "Tuo", "value": '{"index":0}', "type": "status"},
            {"id": "color_mkxfagvd", "text": "Lenny", "value": '{"index":1}', "type": "status"},
            {"id": "color_mkxfdhzv", "text": "Robin", "value": '{"index":2}', "type": "status"},
            {"id": "color_mkxfk0mh", "text": "Robin", "value": '{"index":2}', "type": "status"},
            {"id": "color_mkxfvdj3", "text": "Robin", "value": '{"index":2}', "type": "status"},
            {"id": "date_mkxfdt3d", "text": "2026-05-01", "value": '{"date":"2026-05-01"}', "type": "date"},
            {"id": "date_mkxfjy8s", "text": "2026-05-03", "value": '{"date":"2026-05-03"}', "type": "date"},
            {"id": "date_mkxfyb3x", "text": "2026-05-04", "value": '{"date":"2026-05-04"}', "type": "date"},
            {"id": "date_mkxfregq", "text": "2026-05-05", "value": '{"date":"2026-05-05"}', "type": "date"},
            {"id": "pulse_id_mkxf8pt9", "text": "12345", "value": '{"item_id":"12345"}', "type": "item_id"},
        ],
    }
    if overrides:
        base.update(overrides)
    return base


class TestParseWorkOrder:
    def test_basic_fields(self):
        wo = parse_work_order(_make_wo_item())
        assert wo.id == "12345"
        assert wo.name == "[開發]帳單品項新增狀態"
        assert wo.client == "JGB, 資育"
        assert wo.type == "開發"
        assert wo.pm == "Tuo"
        assert wo.order_number == "12345"

    def test_person_fields(self):
        wo = parse_work_order(_make_wo_item())
        assert wo.developer == "Lenny"
        assert wo.tester == "Robin"
        assert wo.test_completed_by == "Robin"
        assert wo.closed_by == "Robin"

    def test_date_fields(self):
        wo = parse_work_order(_make_wo_item())
        assert wo.assign_date == date(2026, 5, 1)
        assert wo.test_assign_date == date(2026, 5, 3)
        assert wo.test_complete_date == date(2026, 5, 4)
        assert wo.close_date == date(2026, 5, 5)

    def test_computed_status(self):
        wo = parse_work_order(_make_wo_item())
        assert wo.status == "已結案"
        assert wo.total_days == 4

    def test_null_values_use_defaults(self):
        item = {
            "id": "99",
            "name": "empty item",
            "column_values": [
                {"id": "dropdown_mkkzznt3", "text": None, "value": None, "type": "dropdown"},
                {"id": "color_mkxfd8jn", "text": "", "value": None, "type": "status"},
                {"id": "color_mkxfxqs2", "text": "", "value": None, "type": "status"},
                {"id": "color_mkxfagvd", "text": None, "value": None, "type": "status"},
                {"id": "color_mkxfdhzv", "text": "", "value": None, "type": "status"},
                {"id": "color_mkxfk0mh", "text": "", "value": None, "type": "status"},
                {"id": "color_mkxfvdj3", "text": None, "value": None, "type": "status"},
                {"id": "date_mkxfdt3d", "text": "", "value": None, "type": "date"},
                {"id": "date_mkxfjy8s", "text": "", "value": None, "type": "date"},
                {"id": "date_mkxfyb3x", "text": "", "value": None, "type": "date"},
                {"id": "date_mkxfregq", "text": "", "value": None, "type": "date"},
                {"id": "pulse_id_mkxf8pt9", "text": "99", "value": '{"item_id":"99"}', "type": "item_id"},
            ],
        }
        wo = parse_work_order(item)
        assert wo.client == "未指定"
        assert wo.developer == "未指定"
        assert wo.assign_date is None
        assert wo.status == "未指派"

    def test_missing_columns_graceful(self):
        item = {"id": "1", "name": "minimal", "column_values": []}
        wo = parse_work_order(item)
        assert wo.id == "1"
        assert wo.client == "未指定"
        assert wo.developer == "未指定"


# === Campaign parsing ===

def _make_campaign_item() -> dict:
    return {
        "id": "c100",
        "name": "20260213_FB_PLI_馬年賀歲卡",
        "column_values": [
            {"id": "person", "text": "Alice", "value": '{"personsAndTeams":[{"id":99367313}]}', "type": "people"},
            {"id": "color_mm0dy0by", "text": "Holiday", "value": '{"index":1}', "type": "status"},
            {"id": "date_mm0dmy4j", "text": "2026-02-13", "value": '{"date":"2026-02-13"}', "type": "date"},
            {"id": "color_mm0dtqem", "text": "Direct-Go", "value": '{"index":6}', "type": "status"},
            {"id": "color_mm0gy6kv", "text": "Completed", "value": '{"index":1}', "type": "status"},
            {"id": "platform_1", "text": "Facebook", "value": '{"index":0}', "type": "status"},
            {"id": "boolean_mm1397yf", "text": "", "value": '{"checked":false}', "type": "checkbox"},
            {"id": "color_mm0fa2jj", "text": "ZH", "value": '{"index":0}', "type": "status"},
        ],
        "subitems": [
            {"id": "s1", "name": "Copywriting", "column_values": [
                {"id": "status", "text": "Done", "value": '{"index":1}', "type": "status"},
                {"id": "files", "text": "", "value": None, "type": "file"},
            ]},
            {"id": "s2", "name": "Visual", "column_values": [
                {"id": "status", "text": "Done", "value": '{"index":1}', "type": "status"},
                {"id": "files", "text": "img.png", "value": '{"files":[]}', "type": "file"},
            ]},
        ],
        "group": {"id": "g1", "title": "FB｜JGB Smart Property"},
    }


class TestParseCampaign:
    def test_basic_fields(self):
        c = parse_campaign(_make_campaign_item())
        assert c.id == "c100"
        assert c.name == "20260213_FB_PLI_馬年賀歲卡"
        assert c.owner == "Alice"
        assert c.content_type == "Holiday"
        assert c.publish_date == date(2026, 2, 13)
        assert c.platform == "Facebook"

    def test_status_fields(self):
        c = parse_campaign(_make_campaign_item())
        assert c.review_status == "Direct-Go"
        assert c.completion_status == "Completed"

    def test_ads_flag_false(self):
        c = parse_campaign(_make_campaign_item())
        assert c.has_ads is False

    def test_group_name(self):
        c = parse_campaign(_make_campaign_item())
        assert c.group_name == "FB｜JGB Smart Property"

    def test_subitems_parsed(self):
        c = parse_campaign(_make_campaign_item())
        assert len(c.subitems) == 2
        assert c.subitems[0].subitem_type == "copywriting"
        assert c.subitems[1].subitem_type == "visual"
        assert c.subitems[0].status == "Done"

    def test_material_completeness(self):
        c = parse_campaign(_make_campaign_item())
        assert c.material_completeness == 100.0

    def test_is_not_template(self):
        c = parse_campaign(_make_campaign_item())
        assert c.is_template is False

    def test_has_files_detection(self):
        c = parse_campaign(_make_campaign_item())
        assert c.subitems[0].has_files is False
        assert c.subitems[1].has_files is True

    def test_null_values(self):
        item = {
            "id": "c0", "name": "empty",
            "column_values": [
                {"id": "person", "text": "", "value": None, "type": "people"},
                {"id": "color_mm0dy0by", "text": None, "value": None, "type": "status"},
                {"id": "date_mm0dmy4j", "text": "", "value": None, "type": "date"},
                {"id": "color_mm0dtqem", "text": None, "value": None, "type": "status"},
                {"id": "color_mm0gy6kv", "text": None, "value": None, "type": "status"},
                {"id": "platform_1", "text": None, "value": None, "type": "status"},
                {"id": "boolean_mm1397yf", "text": "", "value": '{"checked":false}', "type": "checkbox"},
                {"id": "color_mm0fa2jj", "text": None, "value": None, "type": "status"},
            ],
            "subitems": [],
            "group": {"id": "g1", "title": "FB"},
        }
        c = parse_campaign(item)
        assert c.owner == "未指定"
        assert c.content_type == "未指定"
        assert c.publish_date is None


# === Template filtering ===

class TestFilterTemplates:
    def test_filters_out_templates(self):
        items = [_make_campaign_item()]
        # Add a template item
        template_item = _make_campaign_item()
        template_item["id"] = "t1"
        template_item["column_values"] = [
            {"id": "person", "text": "", "value": None, "type": "people"},
            {"id": "color_mm0dy0by", "text": "Trip-Notice", "value": None, "type": "status"},
            {"id": "date_mm0dmy4j", "text": "", "value": None, "type": "date"},
            {"id": "color_mm0dtqem", "text": "Cancelled", "value": None, "type": "status"},
            {"id": "color_mm0gy6kv", "text": "Paused", "value": None, "type": "status"},
            {"id": "platform_1", "text": None, "value": None, "type": "status"},
            {"id": "boolean_mm1397yf", "text": "", "value": '{"checked":false}', "type": "checkbox"},
            {"id": "color_mm0fa2jj", "text": None, "value": None, "type": "status"},
        ]
        template_item["subitems"] = []
        template_item["group"] = {"id": "g1", "title": "FB"}
        items.append(template_item)

        campaigns = [parse_campaign(i) for i in items]
        filtered = filter_templates(campaigns)
        assert len(filtered) == 1
        assert filtered[0].id == "c100"
