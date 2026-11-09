"""Tests for the billing resource."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from veniceresch import VeniceGoneError


async def test_balance(mock_api, async_client):
    # model_construct tolerates minimal bodies — extras fall through to
    # __pydantic_extra__ and known-field validation is skipped.
    mock_api.get("/billing/balance").respond(200, json={"VCU": 42, "USD": 1.23})
    result = await async_client.billing.balance()
    assert result.model_extra == {"VCU": 42, "USD": 1.23}


# ---- usage_history ---------------------------------------------------------


async def test_usage_history_first_page_translates_filters(mock_api, async_client):
    route = mock_api.get("/billing/usage-history").respond(
        200, json={"data": [{"sku": "llm"}], "nextCursor": "abc_123"}
    )
    page = await async_client.billing.usage_history(
        currency="DIEM",
        start_timestamp="2026-10-01T00:00:00Z",
        end_timestamp="2026-11-01T00:00:00Z",
        page_size=50,
    )
    params = route.calls.last.request.url.params
    assert dict(params) == {
        "currency": "DIEM",
        "startTimestamp": "2026-10-01T00:00:00Z",  # snake_case → camelCase
        "endTimestamp": "2026-11-01T00:00:00Z",
        "pageSize": "50",
    }
    assert page.nextCursor == "abc_123"
    assert page.data == [{"sku": "llm"}]


async def test_usage_history_no_args_sends_no_query(mock_api, async_client):
    route = mock_api.get("/billing/usage-history").respond(
        200, json={"data": [], "nextCursor": None}
    )
    page = await async_client.billing.usage_history()
    assert route.calls.last.request.url.query == b""
    assert page.nextCursor is None


async def test_usage_history_cursor_only(mock_api, async_client):
    route = mock_api.get("/billing/usage-history").respond(
        200, json={"data": [], "nextCursor": None}
    )
    await async_client.billing.usage_history(cursor="tok-1")
    assert dict(route.calls.last.request.url.params) == {"cursor": "tok-1"}


async def test_usage_history_rejects_cursor_with_filters(mock_api, async_client):
    route = mock_api.get("/billing/usage-history")
    with pytest.raises(ValueError, match="cursor"):
        await async_client.billing.usage_history(cursor="tok", currency="USD")
    assert not route.called


def test_usage_history_aware_datetime_rendered_as_utc_z(mock_api, sync_client):
    route = mock_api.get("/billing/usage-history").respond(
        200, json={"data": [], "nextCursor": None}
    )
    plus_two = timezone(timedelta(hours=2))
    sync_client.billing.usage_history(
        start_timestamp=datetime(2026, 10, 1, 2, 0, tzinfo=plus_two),
        end_timestamp=datetime(2026, 10, 2, tzinfo=timezone.utc),
    )
    params = route.calls.last.request.url.params
    assert params["startTimestamp"] == "2026-10-01T00:00:00Z"
    assert params["endTimestamp"] == "2026-10-02T00:00:00Z"


def test_usage_history_rejects_naive_datetime(mock_api, sync_client):
    with pytest.raises(ValueError, match="timezone-aware"):
        sync_client.billing.usage_history(start_timestamp=datetime(2026, 10, 1))


async def test_usage_history_csv_reads_cursor_from_header(mock_api, async_client):
    route = mock_api.get("/billing/usage-history").respond(
        200,
        content=b"timestamp,sku,amount\n2026-10-01T00:00:00Z,llm,0.1\n",
        headers={
            "Content-Type": "text/csv",
            "x-next-cursor": "next_tok",
            "Content-Disposition": (
                'attachment; filename="billing-usage-history-20261109T120000000Z.csv"'
            ),
        },
    )
    page = await async_client.billing.usage_history_csv(currency="USD")
    assert route.calls.last.request.headers["accept"] == "text/csv"
    assert page.content.startswith(b"timestamp,sku")
    assert page.next_cursor == "next_tok"
    assert page.filename == "billing-usage-history-20261109T120000000Z.csv"


def test_usage_history_csv_last_page_has_no_cursor(mock_api, sync_client):
    mock_api.get("/billing/usage-history").respond(
        200, content=b"timestamp\n", headers={"Content-Type": "text/csv"}
    )
    page = sync_client.billing.usage_history_csv(cursor="tok")
    assert page.next_cursor is None
    assert page.filename is None


async def test_usage_analytics(mock_api, async_client):
    route = mock_api.get("/billing/usage-analytics").respond(200, json={"totals": {}})
    await async_client.billing.usage_analytics(lookback="30d")
    assert b"lookback=30d" in route.calls.last.request.url.query


# ---- retired /billing/usage --------------------------------------------------


async def test_usage_is_gone_without_network_call(mock_api, async_client):
    route = mock_api.get("/billing/usage")
    with (
        pytest.warns(DeprecationWarning, match="usage_history"),
        pytest.raises(VeniceGoneError) as info,
    ):
        await async_client.billing.usage(currency="USD", limit=50)
    assert info.value.status_code == 410
    assert "usage-history" in str(info.value) or "usage_history" in str(info.value)
    assert not route.called


def test_iter_usage_is_gone_sync(mock_api, sync_client):
    route = mock_api.get("/billing/usage")
    with (
        pytest.warns(DeprecationWarning, match="iter_usage_history"),
        pytest.raises(VeniceGoneError),
    ):
        sync_client.billing.iter_usage()
    assert not route.called


def test_usage_is_gone_sync(sync_client):
    with pytest.warns(DeprecationWarning), pytest.raises(VeniceGoneError):
        sync_client.billing.usage()


async def test_iter_usage_is_gone_async(async_client):
    with pytest.warns(DeprecationWarning), pytest.raises(VeniceGoneError):
        async_client.billing.iter_usage(limit=10)


def test_deprecated_billing_usage_response_still_importable():
    from veniceresch.types import BillingUsageResponse

    assert BillingUsageResponse(data=[{"a": 1}]).data == [{"a": 1}]
