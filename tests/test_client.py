"""Tests for AsyncVeniceClient and VeniceClient construction and transport."""

from __future__ import annotations

import httpx
import pytest

from venice_sdk import (
    AsyncVeniceClient,
    VeniceAPIError,
    VeniceAuthError,
    VeniceClient,
)
from venice_sdk._client import DEFAULT_BASE_URL

from .conftest import TEST_API_KEY

# ---- construction ---------------------------------------------------------


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("VENICE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="No Venice API key"):
        AsyncVeniceClient()


def test_api_key_read_from_env(monkeypatch):
    monkeypatch.setenv("VENICE_API_KEY", "env-key")
    client = AsyncVeniceClient()
    assert client._api_key == "env-key"


def test_explicit_api_key_overrides_env(monkeypatch):
    monkeypatch.setenv("VENICE_API_KEY", "env-key")
    client = AsyncVeniceClient(api_key="explicit")
    assert client._api_key == "explicit"


def test_base_url_default_and_override():
    c1 = AsyncVeniceClient(api_key="k")
    assert c1.base_url == DEFAULT_BASE_URL
    c2 = AsyncVeniceClient(api_key="k", base_url="https://staging.example/api/v1/")
    assert c2.base_url == "https://staging.example/api/v1"  # trailing slash stripped


def test_auth_header_is_bearer():
    client = AsyncVeniceClient(api_key=TEST_API_KEY)
    assert client._default_headers["Authorization"] == f"Bearer {TEST_API_KEY}"
    assert client._default_headers["User-Agent"].startswith("venice-sdk-python/")


def test_default_headers_merged():
    client = AsyncVeniceClient(
        api_key="k",
        default_headers={"X-Trace-Id": "abc"},
    )
    assert client._default_headers["X-Trace-Id"] == "abc"
    assert "Authorization" in client._default_headers


# ---- async transport ------------------------------------------------------


async def test_async_get_sends_auth_header(mock_api, async_client):
    route = mock_api.get("/models").respond(200, json={"object": "list", "data": []})
    result = await async_client._request_json("GET", "/models")
    assert result == {"object": "list", "data": []}
    assert route.called
    received = route.calls.last.request
    assert received.headers["authorization"] == f"Bearer {TEST_API_KEY}"
    assert received.headers["user-agent"].startswith("venice-sdk-python/")


async def test_async_post_json_body(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(200, json={"id": "cmpl-1", "choices": []})
    body = {"model": "x", "messages": [{"role": "user", "content": "hi"}]}
    await async_client._request_json("POST", "/chat/completions", json_body=body)
    assert route.called
    assert (
        route.calls.last.request.content
        == b'{"model":"x","messages":[{"role":"user","content":"hi"}]}'
    )


async def test_async_bytes_response(mock_api, async_client):
    mock_api.post("/image/upscale").respond(200, content=b"\x89PNG\r\n")
    result = await async_client._request_bytes("POST", "/image/upscale", json_body={"image": "..."})
    assert result == b"\x89PNG\r\n"


async def test_async_error_maps_to_exception(mock_api, async_client):
    mock_api.post("/chat/completions").respond(401, json={"error": "bad key"})
    with pytest.raises(VeniceAuthError) as info:
        await async_client._request_json("POST", "/chat/completions", json_body={})
    assert info.value.status_code == 401


async def test_async_stream_yields_response(mock_api, async_client):
    mock_api.post("/chat/completions").respond(
        200,
        content=b"data: chunk1\n\ndata: chunk2\n\n",
        headers={"content-type": "text/event-stream"},
    )
    chunks = []
    async with async_client._request_stream("POST", "/chat/completions", json_body={}) as response:
        async for chunk in response.aiter_bytes():
            chunks.append(chunk)
    assert b"".join(chunks) == b"data: chunk1\n\ndata: chunk2\n\n"


async def test_async_stream_raises_on_error(mock_api, async_client):
    mock_api.post("/chat/completions").respond(429, json={"error": "slow down"})
    from venice_sdk import VeniceRateLimitError

    with pytest.raises(VeniceRateLimitError):
        async with async_client._request_stream("POST", "/chat/completions", json_body={}):
            pass  # pragma: no cover — should not reach body


async def test_async_context_manager_closes_owned_client(monkeypatch):
    async with AsyncVeniceClient(api_key="k") as client:
        http = client._http
        assert not http.is_closed
    assert http.is_closed


async def test_injected_http_client_not_closed():
    injected = httpx.AsyncClient()
    async with AsyncVeniceClient(api_key="k", http_client=injected) as client:
        assert client._http is injected
    assert not injected.is_closed  # we didn't own it, we didn't close it
    await injected.aclose()


# ---- sync transport -------------------------------------------------------


def test_sync_get(mock_api, sync_client):
    route = mock_api.get("/models").respond(200, json={"object": "list", "data": []})
    result = sync_client._request_json("GET", "/models")
    assert result == {"object": "list", "data": []}
    assert route.called


def test_sync_error_maps(mock_api, sync_client):
    mock_api.get("/models").respond(500, json={"error": "boom"})
    from venice_sdk import VeniceServerError

    with pytest.raises(VeniceServerError):
        sync_client._request_json("GET", "/models")


def test_sync_context_manager_closes():
    with VeniceClient(api_key="k") as client:
        http = client._http
        assert not http.is_closed
    assert http.is_closed


# ---- url building ---------------------------------------------------------


def test_url_for_handles_leading_slash():
    client = AsyncVeniceClient(api_key="k", base_url="https://x/api")
    assert client._url_for("/models") == "https://x/api/models"
    assert client._url_for("models") == "https://x/api/models"


def test_url_for_passes_through_absolute_urls():
    client = AsyncVeniceClient(api_key="k")
    assert client._url_for("https://other/thing") == "https://other/thing"


# ---- non-dict responses ---------------------------------------------------


async def test_request_json_raises_on_non_dict(mock_api, async_client):
    # _request_json promises a dict. If Venice ever returns a top-level array
    # from an endpoint we route through it, surface that loudly rather than
    # silently wrapping — callers should switch to _request_any.
    mock_api.get("/image/styles").respond(200, json=["a", "b", "c"])
    with pytest.raises(TypeError, match="Expected JSON object"):
        await async_client._request_json("GET", "/image/styles")


async def test_request_any_returns_raw_json(mock_api, async_client):
    mock_api.get("/models/traits").respond(200, json=["trait1", "trait2"])
    result = await async_client._request_any("GET", "/models/traits")
    assert result == ["trait1", "trait2"]


# ---- non-API errors still bubble up --------------------------------------


def test_base_exception_class():
    exc = VeniceAPIError("x", status_code=500, error_body={})
    assert isinstance(exc, Exception)
    assert exc.status_code == 500
