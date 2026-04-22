"""Tests for the x402 resource.

The important guarantees here are:
* wallet-address routes carry ``X-Sign-In-With-X`` and do **not** send the
  default ``Authorization`` header;
* ``top_up`` with no payment header triggers Venice's 402 discovery flow,
  which surfaces as :class:`VeniceX402PaymentRequiredError` carrying the
  parsed ``x402_version`` / ``accepts`` fields;
* ``top_up`` with a valid ``payment_header`` returns the success payload.
"""

from __future__ import annotations

import pytest

from veniceresch import VeniceX402PaymentRequiredError


async def test_balance_sends_siwx_not_bearer(mock_api, async_client):
    route = mock_api.get("/x402/balance/0xabc").respond(
        200,
        json={
            "success": True,
            "data": {
                "walletAddress": "0xabc",
                "balanceUsd": 12.5,
                "canConsume": True,
                "minimumTopUpUsd": 5,
                "suggestedTopUpUsd": 10,
            },
        },
    )
    result = await async_client.x402.balance("0xabc", siwx_header="siwx-payload")
    req = route.calls.last.request
    assert req.headers["X-Sign-In-With-X"] == "siwx-payload"
    assert "Authorization" not in req.headers
    assert result.data is not None
    assert result.data["balanceUsd"] == 12.5


async def test_top_up_without_header_raises_discovery(mock_api, async_client):
    mock_api.post("/x402/top-up").respond(
        402,
        json={
            "x402Version": 2,
            "accepts": [
                {
                    "protocol": "x402",
                    "version": 2,
                    "network": "eip155:8453",
                    "asset": "0xUSDC",
                    "amount": "5000000",
                    "payTo": "0xreceiver",
                }
            ],
        },
    )
    with pytest.raises(VeniceX402PaymentRequiredError) as info:
        await async_client.x402.top_up()
    assert info.value.status_code == 402
    assert info.value.x402_version == 2
    assert len(info.value.accepts) == 1
    assert info.value.accepts[0]["network"] == "eip155:8453"


async def test_top_up_with_header_returns_success(mock_api, async_client):
    route = mock_api.post("/x402/top-up").respond(
        200,
        json={
            "success": True,
            "data": {
                "walletAddress": "0xabc",
                "amountCredited": 10,
                "newBalance": 22.5,
                "paymentId": "pay_01",
            },
        },
    )
    result = await async_client.x402.top_up(payment_header="signed-payment")
    req = route.calls.last.request
    assert req.headers["X-402-Payment"] == "signed-payment"
    assert "Authorization" not in req.headers
    assert result.data is not None
    assert result.data["amountCredited"] == 10


async def test_transactions_sends_pagination(mock_api, async_client):
    route = mock_api.get("/x402/transactions/0xabc").respond(
        200,
        json={
            "success": True,
            "data": {
                "walletAddress": "0xabc",
                "currentBalance": 12.35,
                "transactions": [],
                "pagination": {"limit": 25, "offset": 50, "hasMore": False},
            },
        },
    )
    await async_client.x402.transactions(
        "0xabc",
        siwx_header="siwx-payload",
        limit=25,
        offset=50,
    )
    req = route.calls.last.request
    assert req.headers["X-Sign-In-With-X"] == "siwx-payload"
    assert "Authorization" not in req.headers
    assert req.url.params["limit"] == "25"
    assert req.url.params["offset"] == "50"


def test_sync_balance(mock_api, sync_client):
    mock_api.get("/x402/balance/0xabc").respond(
        200,
        json={"success": True, "data": {"walletAddress": "0xabc", "balanceUsd": 0}},
    )
    result = sync_client.x402.balance("0xabc", siwx_header="siwx-payload")
    assert result.data is not None
    assert result.data["walletAddress"] == "0xabc"
