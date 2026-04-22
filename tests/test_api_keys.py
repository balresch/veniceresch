"""Tests for the api_keys resource.

Covers list/create/update/delete/get/rate_limits/rate_limits_log, plus the
web3 challenge + mint flow. The key assertion for the two web3 methods is
that the default ``Authorization: Bearer …`` header is **not** sent — they
run on ``security: []`` per the Venice OpenAPI spec.
"""

from __future__ import annotations


async def test_list(mock_api, async_client):
    route = mock_api.get("/api_keys").respond(
        200,
        json={
            "object": "list",
            "data": [
                {
                    "id": "k1",
                    "apiKeyType": "ADMIN",
                    "description": "example",
                    "last6Chars": "abc123",
                    "createdAt": "2026-04-01T00:00:00Z",
                    "expiresAt": None,
                    "lastUsedAt": None,
                    "consumptionLimits": {"usd": 50, "diem": 10},
                }
            ],
        },
    )
    result = await async_client.api_keys.list()
    assert route.called
    # Admin-scope endpoint: bearer must be present.
    assert route.calls.last.request.headers["Authorization"].startswith("Bearer ")
    assert result.object == "list"
    assert result.data[0]["id"] == "k1"


async def test_get_interpolates_id(mock_api, async_client):
    route = mock_api.get("/api_keys/k1").respond(
        200,
        json={"data": {"id": "k1", "apiKeyType": "ADMIN"}},
    )
    result = await async_client.api_keys.get("k1")
    assert route.called
    assert result.data == {"id": "k1", "apiKeyType": "ADMIN"}


async def test_create_sends_camelcase(mock_api, async_client):
    route = mock_api.post("/api_keys").respond(
        200,
        json={
            "success": True,
            "data": {
                "id": "k1",
                "apiKey": "vn_raw_key",
                "apiKeyType": "ADMIN",
                "description": "example",
                "consumptionLimit": {"usd": 50},
                "expiresAt": None,
            },
        },
    )
    result = await async_client.api_keys.create(
        api_key_type="ADMIN",
        description="example",
        consumption_limit={"usd": 50, "diem": 10},
        expires_at="2027-01-01T00:00:00Z",
    )
    body = route.calls.last.request.content
    import json as _json

    sent = _json.loads(body)
    assert sent == {
        "apiKeyType": "ADMIN",
        "description": "example",
        "consumptionLimit": {"usd": 50, "diem": 10},
        "expiresAt": "2027-01-01T00:00:00Z",
    }
    assert result.success is True
    assert result.data is not None
    assert result.data["apiKey"] == "vn_raw_key"


async def test_update_partial_fields(mock_api, async_client):
    route = mock_api.patch("/api_keys").respond(
        200,
        json={"success": True, "data": {"id": "k1", "description": "renamed"}},
    )
    await async_client.api_keys.update(id="k1", description="renamed")
    import json as _json

    sent = _json.loads(route.calls.last.request.content)
    # Only id + description — no consumptionLimit / expiresAt keys when None.
    assert sent == {"id": "k1", "description": "renamed"}


async def test_delete_passes_id_as_query_param(mock_api, async_client):
    route = mock_api.delete("/api_keys").respond(200, json={"success": True})
    result = await async_client.api_keys.delete("k1")
    assert route.calls.last.request.url.params["id"] == "k1"
    assert result.success is True


async def test_rate_limits(mock_api, async_client):
    mock_api.get("/api_keys/rate_limits").respond(
        200,
        json={
            "data": {
                "accessPermitted": True,
                "apiTier": {"id": "paid", "isCharged": True},
                "balances": {"USD": 50.23, "DIEM": 100.023},
                "keyExpiration": None,
                "nextEpochBegins": "2026-05-01T00:00:00Z",
                "rateLimits": [],
            }
        },
    )
    result = await async_client.api_keys.rate_limits()
    assert result.data is not None
    assert result.data["accessPermitted"] is True
    assert result.data["balances"]["DIEM"] == 100.023


async def test_rate_limits_log(mock_api, async_client):
    mock_api.get("/api_keys/rate_limits/log").respond(
        200,
        json={
            "object": "list",
            "data": [
                {
                    "apiKeyId": "k1",
                    "modelId": "m1",
                    "rateLimitTier": "paid",
                    "rateLimitType": "RPM",
                    "timestamp": "2026-04-01T12:00:00Z",
                }
            ],
        },
    )
    result = await async_client.api_keys.rate_limits_log()
    assert result.data[0]["rateLimitType"] == "RPM"


async def test_web3_challenge_strips_bearer(mock_api, async_client):
    route = mock_api.get("/api_keys/generate_web3_key").respond(
        200,
        json={"success": True, "data": {"token": "challenge-jwt"}},
    )
    result = await async_client.api_keys.generate_web3_key_challenge()
    # security: [] — the default bearer MUST NOT be sent.
    assert "Authorization" not in route.calls.last.request.headers
    assert result.data is not None
    assert result.data["token"] == "challenge-jwt"


async def test_web3_sign_strips_bearer(mock_api, async_client):
    route = mock_api.post("/api_keys/generate_web3_key").respond(
        200,
        json={
            "success": True,
            "data": {
                "id": "k2",
                "apiKey": "vn_web3_key",
                "apiKeyType": "INFERENCE",
                "consumptionLimit": {},
                "expiresAt": None,
            },
        },
    )
    result = await async_client.api_keys.generate_web3_key(
        api_key_type="INFERENCE",
        address="0xabc",
        signature="0xsig",
        token="challenge-jwt",
        description="wallet key",
    )
    assert "Authorization" not in route.calls.last.request.headers
    import json as _json

    sent = _json.loads(route.calls.last.request.content)
    assert sent == {
        "apiKeyType": "INFERENCE",
        "address": "0xabc",
        "signature": "0xsig",
        "token": "challenge-jwt",
        "description": "wallet key",
    }
    assert result.data is not None
    assert result.data["apiKey"] == "vn_web3_key"


def test_sync_list(mock_api, sync_client):
    mock_api.get("/api_keys").respond(200, json={"object": "list", "data": []})
    result = sync_client.api_keys.list()
    assert result.data == []
