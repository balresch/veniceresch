"""``/characters`` resource: list, fetch, and read reviews.

All three methods are GETs. Query parameters follow Venice's camelCase
spelling (``isAdult``, ``sortBy``, ``pageSize``, …); the Python API
accepts snake_case kwargs and translates them before the HTTP call —
same convention as ``model_id → modelId`` for ``image/multi-edit``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from veniceresch.types import (
    CharacterDetailResponse,
    CharacterListResponse,
    CharacterReviewsResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


# snake_case kwarg → swagger query param name. Kwargs not in this map are
# passed through unchanged (``categories``, ``limit``, ``offset``, ``search``,
# ``tags``).
_QUERY_RENAME = {
    "is_adult": "isAdult",
    "is_pro": "isPro",
    "is_web_enabled": "isWebEnabled",
    "model_id": "modelId",
    "sort_by": "sortBy",
    "sort_order": "sortOrder",
    "page_size": "pageSize",
}

# Venice's ``isAdult`` / ``isPro`` / ``isWebEnabled`` are string enums
# ("true" / "false"), not booleans.
_BOOL_AS_STRING = {"is_adult", "is_pro", "is_web_enabled"}


def _build_list_params(**kwargs: Any) -> dict[str, Any] | None:
    params: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is None:
            continue
        if key in _BOOL_AS_STRING and isinstance(value, bool):
            value = "true" if value else "false"
        params[_QUERY_RENAME.get(key, key)] = value
    return params or None


def _build_reviews_params(*, page: int | None, page_size: int | None) -> dict[str, Any] | None:
    params: dict[str, Any] = {}
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["pageSize"] = page_size
    return params or None


class AsyncCharactersResource:
    """Async characters resource. Accessed via ``client.characters``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        categories: list[str] | None = None,
        is_adult: bool | None = None,
        is_pro: bool | None = None,
        is_web_enabled: bool | None = None,
        limit: int | None = None,
        model_id: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        tags: list[str] | None = None,
    ) -> CharacterListResponse:
        params = _build_list_params(
            categories=categories,
            is_adult=is_adult,
            is_pro=is_pro,
            is_web_enabled=is_web_enabled,
            limit=limit,
            model_id=model_id,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            tags=tags,
        )
        raw = await self._client._request_json("GET", "/characters", params=params)
        return CharacterListResponse.model_validate(raw)

    async def get(self, slug: str) -> CharacterDetailResponse:
        raw = await self._client._request_json("GET", f"/characters/{slug}")
        return CharacterDetailResponse.model_validate(raw)

    async def reviews(
        self,
        slug: str,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> CharacterReviewsResponse:
        params = _build_reviews_params(page=page, page_size=page_size)
        raw = await self._client._request_json(
            "GET",
            f"/characters/{slug}/reviews",
            params=params,
        )
        return CharacterReviewsResponse.model_validate(raw)


class CharactersResource:
    """Sync characters resource. Accessed via ``client.characters``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def list(
        self,
        *,
        categories: list[str] | None = None,
        is_adult: bool | None = None,
        is_pro: bool | None = None,
        is_web_enabled: bool | None = None,
        limit: int | None = None,
        model_id: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        tags: list[str] | None = None,
    ) -> CharacterListResponse:
        params = _build_list_params(
            categories=categories,
            is_adult=is_adult,
            is_pro=is_pro,
            is_web_enabled=is_web_enabled,
            limit=limit,
            model_id=model_id,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            tags=tags,
        )
        raw = self._client._request_json("GET", "/characters", params=params)
        return CharacterListResponse.model_validate(raw)

    def get(self, slug: str) -> CharacterDetailResponse:
        raw = self._client._request_json("GET", f"/characters/{slug}")
        return CharacterDetailResponse.model_validate(raw)

    def reviews(
        self,
        slug: str,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> CharacterReviewsResponse:
        params = _build_reviews_params(page=page, page_size=page_size)
        raw = self._client._request_json(
            "GET",
            f"/characters/{slug}/reviews",
            params=params,
        )
        return CharacterReviewsResponse.model_validate(raw)


__all__ = ["AsyncCharactersResource", "CharactersResource"]
