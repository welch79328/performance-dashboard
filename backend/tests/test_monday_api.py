import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.services.monday_api import MondayAPIService


@pytest.fixture
def service():
    return MondayAPIService(api_token="test-token")


# === 2.1 GraphQL API + pagination ===

class TestFetchBoardItems:
    def test_single_page(self, service):
        mock_response = {
            "data": {
                "boards": [{
                    "items_page": {
                        "cursor": None,
                        "items": [
                            {"id": "1", "name": "item1", "column_values": []},
                            {"id": "2", "name": "item2", "column_values": []},
                        ]
                    }
                }]
            }
        }

        with patch.object(service, "_graphql_request", new_callable=AsyncMock, return_value=mock_response):
            items = asyncio.get_event_loop().run_until_complete(
                service.fetch_board_items("123")
            )
            assert len(items) == 2
            assert items[0]["id"] == "1"

    def test_multi_page_pagination(self, service):
        page1 = {
            "data": {
                "boards": [{
                    "items_page": {
                        "cursor": "cursor_abc",
                        "items": [{"id": "1", "name": "item1", "column_values": []}]
                    }
                }]
            }
        }
        page2 = {
            "data": {
                "next_items_page": {
                    "cursor": None,
                    "items": [{"id": "2", "name": "item2", "column_values": []}]
                }
            }
        }

        with patch.object(service, "_graphql_request", new_callable=AsyncMock, side_effect=[page1, page2]):
            items = asyncio.get_event_loop().run_until_complete(
                service.fetch_board_items("123")
            )
            assert len(items) == 2
            assert items[1]["id"] == "2"

    def test_authorization_header(self, service):
        assert service.api_token == "test-token"


class TestFetchBoardItemsWithSubitems:
    def test_campaign_items_include_subitems_and_group(self, service):
        mock_response = {
            "data": {
                "boards": [{
                    "items_page": {
                        "cursor": None,
                        "items": [{
                            "id": "1",
                            "name": "post1",
                            "column_values": [],
                            "subitems": [
                                {"id": "s1", "name": "Copywriting", "column_values": []}
                            ],
                            "group": {"id": "g1", "title": "FB｜JGB Smart Property"}
                        }]
                    }
                }]
            }
        }

        with patch.object(service, "_graphql_request", new_callable=AsyncMock, return_value=mock_response):
            items = asyncio.get_event_loop().run_until_complete(
                service.fetch_board_items_with_subitems("18398984308")
            )
            assert len(items) == 1
            assert items[0]["subitems"][0]["name"] == "Copywriting"
            assert items[0]["group"]["title"] == "FB｜JGB Smart Property"


class TestRetryLogic:
    def test_retry_on_failure(self, service):
        fail_response = Exception("Connection error")
        success_response = {
            "data": {
                "boards": [{
                    "items_page": {
                        "cursor": None,
                        "items": [{"id": "1", "name": "ok", "column_values": []}]
                    }
                }]
            }
        }

        with patch.object(
            service, "_graphql_request", new_callable=AsyncMock,
            side_effect=[fail_response, fail_response, success_response]
        ):
            items = asyncio.get_event_loop().run_until_complete(
                service.fetch_board_items("123")
            )
            assert len(items) == 1

    def test_max_retries_exceeded(self, service):
        with patch.object(
            service, "_graphql_request", new_callable=AsyncMock,
            side_effect=Exception("fail")
        ):
            with pytest.raises(Exception, match="fail"):
                asyncio.get_event_loop().run_until_complete(
                    service.fetch_board_items("123")
                )


# === 2.2 Users + sync_all + cache ===

class TestFetchUsers:
    def test_fetch_users(self, service):
        mock_response = {
            "data": {
                "users": [
                    {"id": "1", "name": "Lenny", "email": "lenny@test.com"},
                    {"id": "2", "name": "Alice", "email": "alice@test.com"},
                ]
            }
        }

        with patch.object(service, "_graphql_request", new_callable=AsyncMock, return_value=mock_response):
            users = asyncio.get_event_loop().run_until_complete(
                service.fetch_users()
            )
            assert len(users) == 2
            assert users[0]["name"] == "Lenny"


class TestSyncAll:
    def test_sync_all_returns_all_data(self, service):
        wo_response = {
            "data": {"boards": [{"items_page": {"cursor": None, "items": [
                {"id": "wo1", "name": "工單1", "column_values": []}
            ]}}]}
        }
        camp_response = {
            "data": {"boards": [{"items_page": {"cursor": None, "items": [
                {"id": "c1", "name": "Campaign1", "column_values": [], "subitems": [], "group": {"id": "g1", "title": "FB"}}
            ]}}]}
        }
        user_response = {
            "data": {"users": [{"id": "u1", "name": "Lenny", "email": "l@t.com"}]}
        }

        with patch.object(
            service, "_graphql_request", new_callable=AsyncMock,
            side_effect=[wo_response, camp_response, user_response]
        ):
            result = asyncio.get_event_loop().run_until_complete(service.sync_all())
            assert len(result["work_orders"]) == 1
            assert len(result["campaigns"]) == 1
            assert len(result["users"]) == 1

    def test_cache_prevents_duplicate_calls(self, service):
        wo_response = {
            "data": {"boards": [{"items_page": {"cursor": None, "items": []}}]}
        }
        camp_response = {
            "data": {"boards": [{"items_page": {"cursor": None, "items": []}}]}
        }
        user_response = {"data": {"users": []}}

        mock = AsyncMock(side_effect=[wo_response, camp_response, user_response])

        with patch.object(service, "_graphql_request", mock):
            r1 = asyncio.get_event_loop().run_until_complete(service.sync_all())
            r2 = asyncio.get_event_loop().run_until_complete(service.sync_all())
            # Second call should use cache, so _graphql_request called only 3 times (not 6)
            assert mock.call_count == 3

    def test_clear_cache(self, service):
        wo_response = {
            "data": {"boards": [{"items_page": {"cursor": None, "items": []}}]}
        }
        camp_response = {
            "data": {"boards": [{"items_page": {"cursor": None, "items": []}}]}
        }
        user_response = {"data": {"users": []}}

        mock = AsyncMock(side_effect=[
            wo_response, camp_response, user_response,
            wo_response, camp_response, user_response,
        ])

        with patch.object(service, "_graphql_request", mock):
            asyncio.get_event_loop().run_until_complete(service.sync_all())
            service.clear_cache()
            asyncio.get_event_loop().run_until_complete(service.sync_all())
            assert mock.call_count == 6
