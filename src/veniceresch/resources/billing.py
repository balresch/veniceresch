"""``/billing/*`` resource: balance, usage history, usage analytics.

``/billing/usage`` (page-based) was sunset by Venice on 2026-09-16 and now
answers every request with HTTP 410. Its replacement,
``/billing/usage-history``, is a cursor walk: the first request carries the
filters, each response carries a ``nextCursor``, and a continuation request
sends *only* that cursor (the filters travel inside it). ``usage()`` /
``iter_usage()`` are kept as deprecated stubs that raise
:class:`~veniceresch._errors.VeniceGoneError` without a network call.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, NoReturn

from typing_extensions import deprecated

from veniceresch._errors import VeniceGoneError
from veniceresch.pagination import AsyncPaginator, Paginator
from veniceresch.types import (
    BillingBalanceResponse,
    BillingUsageAnalyticsResponse,
    BillingUsageHistoryCsvPage,
    BillingUsageHistoryResponse,
)

if TYPE_CHECKING:
    import httpx

    from veniceresch._client import AsyncVeniceClient, VeniceClient


_USAGE_HISTORY_PATH = "/billing/usage-history"
_USAGE_GONE_MESSAGE = (
    "GET /billing/usage was sunset by Venice on 2026-09-16 and no longer returns "
    "data. Use billing.usage_history() / billing.iter_usage_history() instead: "
    "replace page/limit with page_size plus the returned next cursor, and "
    "start_date/end_date with start_timestamp/end_timestamp."
)
_FILENAME_RE = re.compile(r'filename="?([^";]+)"?')

Timestamp = str | datetime


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


def _usage_gone() -> NoReturn:
    raise VeniceGoneError(
        _USAGE_GONE_MESSAGE,
        status_code=410,
        error_body={"error": _USAGE_GONE_MESSAGE},
        link=_USAGE_HISTORY_PATH,
    )


def _format_timestamp(value: Timestamp | None, name: str) -> str | None:
    """Render a timestamp the way ``/billing/usage-history`` requires.

    Venice wants ISO 8601 UTC with a ``Z`` suffix. Strings pass through
    verbatim. Timezone-aware datetimes are converted to UTC and rendered with
    ``Z`` (``datetime.isoformat()`` would emit ``+00:00``). Naive datetimes are
    rejected rather than guessed at.
    """
    if value is None or isinstance(value, str):
        return value
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{name} must be timezone-aware (e.g. datetime(..., tzinfo=timezone.utc)); "
            "got a naive datetime."
        )
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _usage_history_params(
    *,
    currency: str | None,
    start_timestamp: Timestamp | None,
    end_timestamp: Timestamp | None,
    page_size: int | None,
    cursor: str | None,
) -> dict[str, Any]:
    filters = _clean_params(
        {
            "currency": currency,
            "startTimestamp": _format_timestamp(start_timestamp, "start_timestamp"),
            "endTimestamp": _format_timestamp(end_timestamp, "end_timestamp"),
            "pageSize": page_size,
        }
    )
    if cursor is not None:
        # Venice rejects filters sent alongside a cursor (they travel inside
        # it); fail before the round-trip with a clearer message than a 400.
        if filters:
            raise ValueError(
                "cursor= cannot be combined with filter arguments "
                f"({', '.join(sorted(filters))}); the cursor already carries the "
                "filters of the walk it continues."
            )
        return {"cursor": cursor}
    return filters


def _history_items(page: BillingUsageHistoryResponse) -> list[dict[str, Any]]:
    # Built via ``model_construct``, so ``data`` holds raw JSON shapes.
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


def _history_next(
    page: BillingUsageHistoryResponse, params: dict[str, Any]
) -> dict[str, Any] | None:
    cursor = getattr(page, "nextCursor", None)
    if isinstance(cursor, str) and cursor:
        return {"cursor": cursor}
    return None


def _csv_page(response: httpx.Response) -> BillingUsageHistoryCsvPage:
    disposition = response.headers.get("content-disposition") or ""
    match = _FILENAME_RE.search(disposition)
    return BillingUsageHistoryCsvPage(
        content=response.content,
        next_cursor=response.headers.get("x-next-cursor") or None,
        filename=match.group(1) if match else None,
    )


class AsyncBillingResource:
    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def balance(self) -> BillingBalanceResponse:
        raw = await self._client._request_json("GET", "/billing/balance")
        return BillingBalanceResponse.model_construct(**raw)

    async def usage_history(
        self,
        *,
        currency: str | None = None,
        start_timestamp: Timestamp | None = None,
        end_timestamp: Timestamp | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
    ) -> BillingUsageHistoryResponse:
        """Fetch one page of ``GET /billing/usage-history``.

        For the first page pass any filters (``currency``, ``start_timestamp``
        inclusive, ``end_timestamp`` exclusive, ``page_size`` 10-1000). For
        later pages pass *only* ``cursor=page.nextCursor`` — combining a cursor
        with filters raises :class:`ValueError`. ``nextCursor`` is ``None`` on
        the last page. Timestamps may be ISO 8601 strings or timezone-aware
        :class:`~datetime.datetime` objects. Entries arrive in ascending
        timestamp order. Prefer :meth:`iter_usage_history` to walk everything.
        """
        params = _usage_history_params(
            currency=currency,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page_size=page_size,
            cursor=cursor,
        )
        raw = await self._client._request_json("GET", _USAGE_HISTORY_PATH, params=params or None)
        return BillingUsageHistoryResponse.model_construct(**raw)

    async def usage_history_csv(
        self,
        *,
        currency: str | None = None,
        start_timestamp: Timestamp | None = None,
        end_timestamp: Timestamp | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
    ) -> BillingUsageHistoryCsvPage:
        """Like :meth:`usage_history`, but returns the page as a CSV export.

        The continuation token is read from the ``x-next-cursor`` response
        header onto :attr:`BillingUsageHistoryCsvPage.next_cursor`.
        """
        params = _usage_history_params(
            currency=currency,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page_size=page_size,
            cursor=cursor,
        )
        response = await self._client._send(
            "GET",
            _USAGE_HISTORY_PATH,
            json_body=None,
            params=params or None,
            headers={"Accept": "text/csv"},
        )
        return _csv_page(response)

    def iter_usage_history(
        self,
        *,
        currency: str | None = None,
        start_timestamp: Timestamp | None = None,
        end_timestamp: Timestamp | None = None,
        page_size: int | None = None,
    ) -> AsyncPaginator[dict[str, Any], BillingUsageHistoryResponse]:
        """Auto-paginated walk over ``/billing/usage-history``.

        ``async for entry in client.billing.iter_usage_history(...)`` yields
        every ledger entry; ``.iter_pages()`` yields each
        :class:`BillingUsageHistoryResponse`. Follows ``nextCursor`` until it
        is ``None``. Arguments are validated now; no HTTP call fires until
        iteration starts.
        """
        initial = _usage_history_params(
            currency=currency,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page_size=page_size,
            cursor=None,
        )

        async def _fetch(params: dict[str, Any]) -> BillingUsageHistoryResponse:
            raw = await self._client._request_json(
                "GET", _USAGE_HISTORY_PATH, params=params or None
            )
            return BillingUsageHistoryResponse.model_construct(**raw)

        return AsyncPaginator(
            fetch=_fetch,
            initial_params=initial,
            extract=_history_items,
            step=_history_next,
        )

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

    @deprecated("billing.usage() is gone (Venice sunset /billing/usage); use usage_history()")
    async def usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        page: int | None = None,
        sort_order: str | None = None,
    ) -> NoReturn:
        """Deprecated: ``/billing/usage`` was sunset on 2026-09-16.

        Always raises :class:`~veniceresch._errors.VeniceGoneError` (no
        network call). Use :meth:`usage_history` / :meth:`iter_usage_history`.
        Removed in 1.0.
        """
        _usage_gone()

    @deprecated(
        "billing.iter_usage() is gone (Venice sunset /billing/usage); use iter_usage_history()"
    )
    def iter_usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 200,
        sort_order: str | None = None,
    ) -> NoReturn:
        """Deprecated: ``/billing/usage`` was sunset on 2026-09-16.

        Always raises :class:`~veniceresch._errors.VeniceGoneError` at call
        time (no network call). Use :meth:`iter_usage_history`. Removed in 1.0.
        """
        _usage_gone()


class BillingResource:
    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def balance(self) -> BillingBalanceResponse:
        raw = self._client._request_json("GET", "/billing/balance")
        return BillingBalanceResponse.model_construct(**raw)

    def usage_history(
        self,
        *,
        currency: str | None = None,
        start_timestamp: Timestamp | None = None,
        end_timestamp: Timestamp | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
    ) -> BillingUsageHistoryResponse:
        """Sync mirror of :meth:`AsyncBillingResource.usage_history`."""
        params = _usage_history_params(
            currency=currency,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page_size=page_size,
            cursor=cursor,
        )
        raw = self._client._request_json("GET", _USAGE_HISTORY_PATH, params=params or None)
        return BillingUsageHistoryResponse.model_construct(**raw)

    def usage_history_csv(
        self,
        *,
        currency: str | None = None,
        start_timestamp: Timestamp | None = None,
        end_timestamp: Timestamp | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
    ) -> BillingUsageHistoryCsvPage:
        """Sync mirror of :meth:`AsyncBillingResource.usage_history_csv`."""
        params = _usage_history_params(
            currency=currency,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page_size=page_size,
            cursor=cursor,
        )
        response = self._client._send(
            "GET",
            _USAGE_HISTORY_PATH,
            json_body=None,
            params=params or None,
            headers={"Accept": "text/csv"},
        )
        return _csv_page(response)

    def iter_usage_history(
        self,
        *,
        currency: str | None = None,
        start_timestamp: Timestamp | None = None,
        end_timestamp: Timestamp | None = None,
        page_size: int | None = None,
    ) -> Paginator[dict[str, Any], BillingUsageHistoryResponse]:
        """Sync mirror of :meth:`AsyncBillingResource.iter_usage_history`."""
        initial = _usage_history_params(
            currency=currency,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page_size=page_size,
            cursor=None,
        )

        def _fetch(params: dict[str, Any]) -> BillingUsageHistoryResponse:
            raw = self._client._request_json("GET", _USAGE_HISTORY_PATH, params=params or None)
            return BillingUsageHistoryResponse.model_construct(**raw)

        return Paginator(
            fetch=_fetch,
            initial_params=initial,
            extract=_history_items,
            step=_history_next,
        )

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

    @deprecated("billing.usage() is gone (Venice sunset /billing/usage); use usage_history()")
    def usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        page: int | None = None,
        sort_order: str | None = None,
    ) -> NoReturn:
        """Sync mirror of :meth:`AsyncBillingResource.usage` (deprecated)."""
        _usage_gone()

    @deprecated(
        "billing.iter_usage() is gone (Venice sunset /billing/usage); use iter_usage_history()"
    )
    def iter_usage(
        self,
        *,
        currency: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 200,
        sort_order: str | None = None,
    ) -> NoReturn:
        """Sync mirror of :meth:`AsyncBillingResource.iter_usage` (deprecated)."""
        _usage_gone()


__all__ = ["AsyncBillingResource", "BillingResource"]
