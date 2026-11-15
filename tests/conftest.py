"""Shared pytest fixtures for veniceresch tests."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from veniceresch import AsyncVeniceClient, VeniceClient
from veniceresch._client import DEFAULT_BASE_URL

TEST_API_KEY = "test-key-abc123"


def pytest_configure(config: pytest.Config) -> None:
    """Refuse to run on a distro system interpreter (GH #18).

    On the dev host, the system Python is shared with a downstream production
    service that imports ``veniceresch`` from it. Running the suite there means
    someone installed into the system interpreter: an editable install breaks
    that service on restart, and a regular one makes pytest test the installed
    release instead of ``src/``. Use the project venv instead. CI runners and
    any venv / conda / pyenv / Homebrew interpreter pass this check.
    """
    if os.environ.get("CI") or os.environ.get("VENICERESCH_ALLOW_SYSTEM_PYTHON") == "1":
        return
    if sys.prefix == sys.base_prefix and sys.prefix in ("/usr", "/usr/local"):
        raise pytest.UsageError(
            f"Running on the system interpreter ({sys.executable}). Develop in the project "
            'venv: python3.13 -m venv .venv && .venv/bin/pip install -e ".[dev]", then '
            "run .venv/bin/pytest. Never pip install veniceresch into the system Python "
            "(see CLAUDE.md, GH #18). Override: VENICERESCH_ALLOW_SYSTEM_PYTHON=1."
        )


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
