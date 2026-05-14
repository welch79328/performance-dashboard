BOARDS: dict[str, dict] = {
    "work_orders": {
        "board_id": "7960591450",
        "name": "工單總表",
        "department": "pm_rd",
        "columns": {
            "client": "dropdown_mkkzznt3",
            "type": "color_mkxfd8jn",
            "pm": "color_mkxfxqs2",
            "developer": "color_mkxfagvd",
            "tester": "color_mkxfdhzv",
            "test_completed_by": "color_mkxfk0mh",
            "closed_by": "color_mkxfvdj3",
            "assign_date": "date_mkxfdt3d",
            "test_assign_date": "date_mkxfjy8s",
            "test_complete_date": "date_mkxfyb3x",
            "close_date": "date_mkxfregq",
            "order_number": "pulse_id_mkxf8pt9",
        },
    },
    "campaigns": {
        "board_id": "18398984308",
        "name": "Campaign Planning & Status",
        "department": "marketing",
        "columns": {
            "owner": "person",
            "content_type": "color_mm0dy0by",
            "publish_date": "date_mm0dmy4j",
            "review_status": "color_mm0dtqem",
            "completion_status": "color_mm0gy6kv",
            "platform": "platform_1",
            "has_ads": "boolean_mm1397yf",
            "language": "color_mm0fa2jj",
        },
    },
}

CAMPAIGN_SUBITEM_COLUMNS: dict[str, str] = {
    "text_content": "text_mm0hrgjg",
    "status": "status",
    "files": "files",
}
