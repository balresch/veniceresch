"""Shared pytest fixtures for venice-sdk tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from venice_sdk import AsyncVeniceClient, VeniceClient
from venice_sdk._client import DEFAULT_BASE_URL

TEST_API_KEY = "test-key-abc123"


@pytest.fixture
def base_url() -> str:
    return DEFAULT_BASE_URL


@pytest.fixture
def mock_api() -> Iterator[respx.Router]:
    """respx router scoped to Venice's base URL. Any un-mocked request fails."""
    with respx.mock(base_url=DEFAULT_BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncVeniceClient]:
    async with AsyncVeniceClient(api_key=TEST_API_KEY) as client:
        yield client


@pytest.fixture
def sync_client() -> Iterator[VeniceClient]:
    with VeniceClient(api_key=TEST_API_KEY) as client:
        yield client


@pytest.fixture
def make_response() -> type[MakeResponse]:
    """Factory for httpx.Response objects — used in error-mapping tests."""
    return MakeResponse


class MakeResponse:
    """Builder for httpx.Response with an attached request (needed by errors)."""

    @staticmethod
    def json(status: int, body: object, *, url: str = "https://example/") -> httpx.Response:
        request = httpx.Request("POST", url)
        return httpx.Response(status, json=body, request=request)

    @staticmethod
    def text(status: int, body: str, *, url: str = "https://example/") -> httpx.Response:
        request = httpx.Request("POST", url)
        return httpx.Response(status, text=body, request=request)
