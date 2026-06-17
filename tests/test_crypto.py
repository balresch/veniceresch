"""Tests for the crypto RPC resource.

Guarantees:
* ``networks`` hits the public endpoint and parses the slug list;
* ``rpc`` mirrors the request shape — dict for a single call, list for a batch;
* ``siwx_header`` swaps Bearer auth for the ``SIGN-IN-WITH-X`` header;
* ``idempotency_key`` is forwarded as the ``Idempotency-Key`` header.
"""

from __future__ import annotations

import json


async def test_networks_is_public(mock_api, async_client):
    route = mock_api.get("/crypto/rpc/networks").respond(
        200,
        json={"networks": ["base-mainnet", "ethereum-mainnet"]},
    )
    result = await async_client.crypto.networks()
    assert result.networks == ["base-mainnet", "ethereum-mainnet"]
    # Public endpoint — we strip the default bearer.
    assert "Authorization" not in route.calls.last.request.headers


async def test_rpc_single_returns_dict(mock_api, async_client):
    route = mock_api.post("/crypto/rpc/ethereum-mainnet").respond(
        200,
        json={"jsonrpc": "2.0", "id": 1, "result": "0x1"},
    )
    req_body = {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
    result = await async_client.crypto.rpc("ethereum-mainnet", req_body)
    assert result == {"jsonrpc": "2.0", "id": 1, "result": "0x1"}
    sent = json.loads(route.calls.last.request.content)
    assert sent == req_body
    # Default bearer auth is used when no siwx header is given.
    assert route.calls.last.request.headers["Authorization"].startswith("Bearer ")


async def test_rpc_batch_returns_list(mock_api, async_client):
    mock_api.post("/crypto/rpc/base-mainnet").respond(
        200,
        json=[
            {"jsonrpc": "2.0", "id": 1, "result": "0x2105"},
            {"jsonrpc": "2.0", "id": 2, "result": "0x10"},
        ],
    )
    batch = [
        {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1},
        {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 2},
    ]
    result = await async_client.crypto.rpc("base-mainnet", batch)
    assert isinstance(result, list)
    assert [item["id"] for item in result] == [1, 2]


async def test_rpc_siwx_and_idempotency_headers(mock_api, async_client):
    route = mock_api.post("/crypto/rpc/base-mainnet").respond(
        200, json={"jsonrpc": "2.0", "id": 1, "result": "0x1"}
    )
    await async_client.crypto.rpc(
        "base-mainnet",
        {"jsonrpc": "2.0", "method": "eth_chainId", "id": 1},
        siwx_header="siwx-payload",
        idempotency_key="abc-123",
    )
    req = route.calls.last.request
    assert req.headers["SIGN-IN-WITH-X"] == "siwx-payload"
    assert req.headers["Idempotency-Key"] == "abc-123"
    # Wallet auth strips the default bearer.
    assert "Authorization" not in req.headers


def test_rpc_sync(mock_api, sync_client):
    mock_api.post("/crypto/rpc/ethereum-mainnet").respond(
        200, json={"jsonrpc": "2.0", "id": 1, "result": "0x1"}
    )
    result = sync_client.crypto.rpc(
        "ethereum-mainnet",
        {"jsonrpc": "2.0", "method": "eth_chainId", "id": 1},
    )
    assert result["result"] == "0x1"


def test_networks_sync(mock_api, sync_client):
    mock_api.get("/crypto/rpc/networks").respond(200, json={"networks": ["base-mainnet"]})
    result = sync_client.crypto.networks()
    assert result.networks == ["base-mainnet"]
