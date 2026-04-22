"""``/billing/*`` resource: balance, usage, usage analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from veniceresch.pagination import AsyncPaginator, Paginator
from veniceresch.types import (
    BillingBalanceResponse,
    BillingUsageAnalyticsResponse,
    BillingUsageResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


def _usage_items(page: BillingUsageResponse) -> list[dict[str, Any]]:
    # ``usage`` is built via ``model_construct``, so fields hold raw JSON shapes.
    # Normalize to plain dicts regardless of what landed there.
    data: Any = getattr(page, "data", None)
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict):
            out.append(item)
        elif hasattr(item, "model_dump"):
            dumped = item.model_dump()
            if isinstance(dumped, dict):
                out.append(dumped)
    return out


def _usage_next(page: BillingUsageResponse, params: dict[str, Any]) -> dict[str, Any] | None:
    pagination: Any = getattr(page, "pagination", None)
    if hasattr(pagination, "model_dump"):
        pagination = pagination.model_dump()
    if not isinstance(pagination, dict):
        pagination = {}
    total_pages = pagination.get("totalPages")
    current_page = pagination.get("page", params["page"])
    if total_pages is not None and current_page >= total_pages:
        return None
    # Fallback for missing / unusual envelope: stop on short page.
    if len(_usage_items(page)) < params["limit"]:
        return None
    return {"limit": params["limit"], "page": params["page"] + 1}


class AsyncBillingResource:
    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def balance(self) -> BillingBalanceResponse:
        raw = await self._client._request_json("GET", "/billing/balance")
        return BillingBalanceResponse.model_construct(**raw)

    async def usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        page: int | None = None,
        sort_order: str | None = None,
    ) -> BillingUsageResponse:
        params = _clean_params(
            {
                "currency": currency,
                "startDate": start_date,
                "endDate": end_date,
                "limit": limit,
                "page": page,
                "sortOrder": sort_order,
            }
        )
        raw = await self._client._request_json("GET", "/billing/usage", params=params or None)
        return BillingUsageResponse.model_construct(**raw)

    async def usage_analytics(
        self,
        *,
        lookback: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> BillingUsageAnalyticsResponse:
        params = _clean_params(
            {
                "lookback": lookback,
                "startDate": start_date,
                "endDate": end_date,
            }
        )
        raw = await self._client._request_json(
            "GET",
            "/billing/usage-analytics",
            params=params or None,
        )
        return BillingUsageAnalyticsResponse.model_construct(**raw)

    def iter_usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 200,
        sort_order: str | None = None,
    ) -> AsyncPaginator[dict[str, Any], BillingUsageResponse]:
        """Auto-paginated iteration over ``/billing/usage``.

        ``async for entry in client.billing.iter_usage()`` yields each
        usage record across all pages. ``iter_pages()`` yields the
        :class:`BillingUsageResponse` per page. No HTTP calls fire
        until iteration starts.
        """

        async def _fetch(params: dict[str, Any]) -> BillingUsageResponse:
            return await self.usage(
                currency=currency,
                start_date=start_date,
                end_date=end_date,
                limit=params["limit"],
                page=params["page"],
                sort_order=sort_order,
            )

        return AsyncPaginator(
            fetch=_fetch,
            initial_params={"limit": limit, "page": 1},
            extract=_usage_items,
            step=_usage_next,
        )


class BillingResource:
    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def balance(self) -> BillingBalanceResponse:
        raw = self._client._request_json("GET", "/billing/balance")
        return BillingBalanceResponse.model_construct(**raw)

    def usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        page: int | None = None,
        sort_order: str | None = None,
    ) -> BillingUsageResponse:
        params = _clean_params(
            {
                "currency": currency,
                "startDate": start_date,
                "endDate": end_date,
                "limit": limit,
                "page": page,
                "sortOrder": sort_order,
            }
        )
        raw = self._client._request_json("GET", "/billing/usage", params=params or None)
        return BillingUsageResponse.model_construct(**raw)

    def usage_analytics(
        self,
        *,
        lookback: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> BillingUsageAnalyticsResponse:
        params = _clean_params(
            {
                "lookback": lookback,
                "startDate": start_date,
                "endDate": end_date,
            }
        )
        raw = self._client._request_json(
            "GET",
            "/billing/usage-analytics",
            params=params or None,
        )
        return BillingUsageAnalyticsResponse.model_construct(**raw)

    def iter_usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 200,
        sort_order: str | None = None,
    ) -> Paginator[dict[str, Any], BillingUsageResponse]:
        """Sync mirror of :meth:`AsyncBillingResource.iter_usage`."""

        def _fetch(params: dict[str, Any]) -> BillingUsageResponse:
            return self.usage(
                currency=currency,
                start_date=start_date,
                end_date=end_date,
                limit=params["limit"],
                page=params["page"],
                sort_order=sort_order,
            )

        return Paginator(
            fetch=_fetch,
            initial_params={"limit": limit, "page": 1},
            extract=_usage_items,
            step=_usage_next,
        )


__all__ = ["AsyncBillingResource", "BillingResource"]
