"""Integration smoke tests — these hit the real Venice API.

Run with ``VENICE_API_KEY=... pytest tests/integration -m integration``.
Skipped by default (no key). Keep these tiny; this is a smoke, not a
regression suite.
"""

from __future__ import annotations

import os

import pytest

from venice_sdk import AsyncVeniceClient

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def api_key() -> str:
    key = os.environ.get("VENICE_API_KEY")
    if not key:
        pytest.skip("VENICE_API_KEY not set — integration tests disabled.")
    return key


async def test_models_list(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.models.list()
        assert "data" in result or "object" in result


async def test_models_list_video(api_key: str) -> None:
    """Regression: community SDK's ModelType Literal excludes "video"."""
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.models.list(type="video")
        # If Venice exposes any video models, data is a non-empty list.
        # If not, we still get a valid 200 — the important thing is no error.
        assert isinstance(result, dict)


async def test_billing_balance(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.billing.balance()
        assert isinstance(result, dict)


async def test_chat_completion_minimal(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        models = await client.models.list(type="text")
        data = models.get("data", [])
        if not data:
            pytest.skip("No text models available on this account.")
        model_id = data[0]["id"]
        result = await client.chat.create(
            model=model_id,
            messages=[{"role": "user", "content": "Say 'pong' and nothing else."}],
            max_tokens=10,
        )
        assert result["choices"][0]["message"]["content"]


async def test_image_styles(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.image.list_styles()
        assert "data" in result or isinstance(result, dict)
