import asyncio
import time
from typing import Any

import httpx
from cachetools import TTLCache

from app.config.column_mapping import BOARDS

MONDAY_API_URL = "https://api.monday.com/v2"
MAX_RETRIES = 3
BASE_DELAY_MS = 1000


class MondayAPIService:
    def __init__(self, api_token: str, cache_ttl: int = 900):
        self.api_token = api_token
        self._cache: TTLCache = TTLCache(maxsize=10, ttl=cache_ttl)

    async def _graphql_request(self, query: str, variables: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload: dict[str, Any] = {"query": query}
            if variables:
                payload["variables"] = variables
            response = await client.post(
                MONDAY_API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": self.api_token,
                },
            )
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                raise RateLimitError(retry_after)
            response.raise_for_status()
            return response.json()

    async def _request_with_retry(self, query: str, variables: dict | None = None) -> dict:
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                return await self._graphql_request(query, variables)
            except RateLimitError as e:
                await asyncio.sleep(e.retry_after)
                last_error = e
            except Exception as e:
                last_error = e
                delay = (BASE_DELAY_MS / 1000) * (2 ** attempt)
                await asyncio.sleep(delay)
        raise last_error  # type: ignore[misc]

    async def fetch_board_items(self, board_id: str) -> list[dict]:
        query = """
        query ($boardId: [ID!]!) {
            boards(ids: $boardId) {
                items_page(limit: 500) {
                    cursor
                    items {
                        id name
                        column_values { id text value type }
                    }
                }
            }
        }
        """
        all_items: list[dict] = []
        result = await self._request_with_retry(query, {"boardId": [board_id]})

        page = result["data"]["boards"][0]["items_page"]
        all_items.extend(page["items"])
        cursor = page.get("cursor")

        while cursor:
            next_query = """
            query ($cursor: String!) {
                next_items_page(cursor: $cursor, limit: 500) {
                    cursor
                    items {
                        id name
                        column_values { id text value type }
                    }
                }
            }
            """
            result = await self._request_with_retry(next_query, {"cursor": cursor})
            page = result["data"]["next_items_page"]
            all_items.extend(page["items"])
            cursor = page.get("cursor")

        return all_items

    async def fetch_board_items_with_subitems(self, board_id: str) -> list[dict]:
        query = """
        query ($boardId: [ID!]!) {
            boards(ids: $boardId) {
                items_page(limit: 500) {
                    cursor
                    items {
                        id name
                        column_values { id text value type }
                        subitems {
                            id name
                            column_values { id text value type }
                        }
                        group { id title }
                    }
                }
            }
        }
        """
        all_items: list[dict] = []
        result = await self._request_with_retry(query, {"boardId": [board_id]})

        page = result["data"]["boards"][0]["items_page"]
        all_items.extend(page["items"])
        cursor = page.get("cursor")

        while cursor:
            next_query = """
            query ($cursor: String!) {
                next_items_page(cursor: $cursor, limit: 500) {
                    cursor
                    items {
                        id name
                        column_values { id text value type }
                        subitems {
                            id name
                            column_values { id text value type }
                        }
                        group { id title }
                    }
                }
            }
            """
            result = await self._request_with_retry(next_query, {"cursor": cursor})
            page = result["data"]["next_items_page"]
            all_items.extend(page["items"])
            cursor = page.get("cursor")

        return all_items

    async def fetch_users(self) -> list[dict]:
        query = '{ users { id name email } }'
        result = await self._request_with_retry(query)
        return result["data"]["users"]

    async def sync_all(self) -> dict[str, list[dict]]:
        cache_key = "sync_all"
        if cache_key in self._cache:
            return self._cache[cache_key]

        wo_board_id = BOARDS["work_orders"]["board_id"]
        camp_board_id = BOARDS["campaigns"]["board_id"]

        work_orders = await self.fetch_board_items(wo_board_id)
        campaigns = await self.fetch_board_items_with_subitems(camp_board_id)
        users = await self.fetch_users()

        result = {
            "work_orders": work_orders,
            "campaigns": campaigns,
            "users": users,
        }
        self._cache[cache_key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    @property
    def last_sync_time(self) -> float | None:
        if "sync_all" in self._cache:
            return time.time()
        return None


class RateLimitError(Exception):
    def __init__(self, retry_after: int = 5):
        self.retry_after = retry_after
        super().__init__(f"Rate limited, retry after {retry_after}s")
