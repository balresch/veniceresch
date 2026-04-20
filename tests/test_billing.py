"""Tests for the billing resource."""

from __future__ import annotations


async def test_balance(mock_api, async_client):
    # model_construct tolerates minimal bodies — extras fall through to
    # __pydantic_extra__ and known-field validation is skipped.
    mock_api.get("/billing/balance").respond(200, json={"VCU": 42, "USD": 1.23})
    result = await async_client.billing.balance()
    assert result.model_extra == {"VCU": 42, "USD": 1.23}


async def test_usage_with_filters(mock_api, async_client):
    route = mock_api.get("/billing/usage").respond(200, json={"entries": []})
    await async_client.billing.usage(
        currency="USD",
        start_date="2026-01-01",
        end_date="2026-01-31",
        limit=50,
    )
    q = route.calls.last.request.url.query
    assert b"currency=USD" in q
    assert b"startDate=2026-01-01" in q  # snake_case → camelCase
    assert b"endDate=2026-01-31" in q
    assert b"limit=50" in q


async def test_usage_no_params_sends_no_query(mock_api, async_client):
    route = mock_api.get("/billing/usage").respond(200, json={"entries": []})
    await async_client.billing.usage()
    assert route.calls.last.request.url.query == b""


async def test_usage_analytics(mock_api, async_client):
    route = mock_api.get("/billing/usage-analytics").respond(200, json={"totals": {}})
    await async_client.billing.usage_analytics(lookback="30d")
    assert b"lookback=30d" in route.calls.last.request.url.query
