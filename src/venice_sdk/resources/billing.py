"""``/billing/*`` resource: balance, usage, usage analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from venice_sdk._client import AsyncVeniceClient, VeniceClient


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


class AsyncBillingResource:
    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def balance(self) -> dict[str, Any]:
        return await self._client._request_json("GET", "/billing/balance")

    async def usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        page: int | None = None,
        sort_order: str | None = None,
    ) -> dict[str, Any]:
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
        return await self._client._request_json("GET", "/billing/usage", params=params or None)

    async def usage_analytics(
        self,
        *,
        lookback: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        params = _clean_params(
            {
                "lookback": lookback,
                "startDate": start_date,
                "endDate": end_date,
            }
        )
        return await self._client._request_json(
            "GET",
            "/billing/usage-analytics",
            params=params or None,
        )


class BillingResource:
    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def balance(self) -> dict[str, Any]:
        return self._client._request_json("GET", "/billing/balance")

    def usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        page: int | None = None,
        sort_order: str | None = None,
    ) -> dict[str, Any]:
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
        return self._client._request_json("GET", "/billing/usage", params=params or None)

    def usage_analytics(
        self,
        *,
        lookback: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        params = _clean_params(
            {
                "lookback": lookback,
                "startDate": start_date,
                "endDate": end_date,
            }
        )
        return self._client._request_json(
            "GET",
            "/billing/usage-analytics",
            params=params or None,
        )


__all__ = ["AsyncBillingResource", "BillingResource"]
