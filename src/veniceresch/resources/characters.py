"""``/characters`` resource: list, fetch, and read reviews.

All three methods are GETs. Query parameters follow Venice's camelCase
spelling (``isAdult``, ``sortBy``, ``pageSize``, …); the Python API
accepts snake_case kwargs and translates them before the HTTP call —
same convention as ``model_id → modelId`` for ``image/multi-edit``.
"""

from __future__ import annotations

from builtins import list as _list
from typing import TYPE_CHECKING, Any

from veniceresch.pagination import AsyncPaginator, Paginator
from veniceresch.types import (
    CharacterDetailResponse,
    CharacterListResponse,
    CharacterReviewsResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient

# ``_list`` aliases the builtin so ``iter_list``'s type annotations don't
# collide with the ``list`` method name in the resource classes — mypy would
# otherwise resolve ``list[str]`` to the method (a function isn't valid as a
# type).


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


def _list_items(page: CharacterListResponse) -> list[dict[str, Any]]:
    return page.data


def _list_next(page: CharacterListResponse, params: dict[str, Any]) -> dict[str, Any] | None:
    # /characters has no pagination envelope — stop on a short/empty page.
    if len(page.data) < params["limit"]:
        return None
    return {"limit": params["limit"], "offset": params["offset"] + params["limit"]}


def _reviews_items(page: CharacterReviewsResponse) -> list[dict[str, Any]]:
    return page.data


def _reviews_next(
    page: CharacterReviewsResponse,
    params: dict[str, Any],
) -> dict[str, Any] | None:
    pagination = page.pagination or {}
    total_pages = pagination.get("totalPages")
    current_page = pagination.get("page", params["page"])
    if total_pages is not None and current_page >= total_pages:
        return None
    # Fallback when the envelope is missing or unusual.
    if len(page.data) < params["page_size"]:
        return None
    return {"page": params["page"] + 1, "page_size": params["page_size"]}


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

    def iter_list(
        self,
        *,
        categories: _list[str] | None = None,
        is_adult: bool | None = None,
        is_pro: bool | None = None,
        is_web_enabled: bool | None = None,
        limit: int = 50,
        model_id: _list[str] | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        tags: _list[str] | None = None,
    ) -> AsyncPaginator[dict[str, Any], CharacterListResponse]:
        """Auto-paginated iteration over ``/characters``.

        ``async for character in client.characters.iter_list()`` yields
        each character dict across all pages. ``iter_pages()`` yields
        the :class:`CharacterListResponse` per page. No HTTP calls fire
        until iteration starts.
        """

        async def _fetch(params: dict[str, Any]) -> CharacterListResponse:
            return await self.list(
                categories=categories,
                is_adult=is_adult,
                is_pro=is_pro,
                is_web_enabled=is_web_enabled,
                limit=params["limit"],
                model_id=model_id,
                offset=params["offset"],
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                tags=tags,
            )

        return AsyncPaginator(
            fetch=_fetch,
            initial_params={"limit": limit, "offset": 0},
            extract=_list_items,
            step=_list_next,
        )

    def iter_reviews(
        self,
        slug: str,
        *,
        page_size: int = 20,
    ) -> AsyncPaginator[dict[str, Any], CharacterReviewsResponse]:
        """Auto-paginated iteration over ``/characters/{slug}/reviews``."""

        async def _fetch(params: dict[str, Any]) -> CharacterReviewsResponse:
            return await self.reviews(
                slug,
                page=params["page"],
                page_size=params["page_size"],
            )

        return AsyncPaginator(
            fetch=_fetch,
            initial_params={"page": 1, "page_size": page_size},
            extract=_reviews_items,
            step=_reviews_next,
        )


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

    def iter_list(
        self,
        *,
        categories: _list[str] | None = None,
        is_adult: bool | None = None,
        is_pro: bool | None = None,
        is_web_enabled: bool | None = None,
        limit: int = 50,
        model_id: _list[str] | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        tags: _list[str] | None = None,
    ) -> Paginator[dict[str, Any], CharacterListResponse]:
        """Sync mirror of :meth:`AsyncCharactersResource.iter_list`."""

        def _fetch(params: dict[str, Any]) -> CharacterListResponse:
            return self.list(
                categories=categories,
                is_adult=is_adult,
                is_pro=is_pro,
                is_web_enabled=is_web_enabled,
                limit=params["limit"],
                model_id=model_id,
                offset=params["offset"],
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                tags=tags,
            )

        return Paginator(
            fetch=_fetch,
            initial_params={"limit": limit, "offset": 0},
            extract=_list_items,
            step=_list_next,
        )

    def iter_reviews(
        self,
        slug: str,
        *,
        page_size: int = 20,
    ) -> Paginator[dict[str, Any], CharacterReviewsResponse]:
        """Sync mirror of :meth:`AsyncCharactersResource.iter_reviews`."""

        def _fetch(params: dict[str, Any]) -> CharacterReviewsResponse:
            return self.reviews(
                slug,
                page=params["page"],
                page_size=params["page_size"],
            )

        return Paginator(
            fetch=_fetch,
            initial_params={"page": 1, "page_size": page_size},
            extract=_reviews_items,
            step=_reviews_next,
        )


__all__ = ["AsyncCharactersResource", "CharactersResource"]
