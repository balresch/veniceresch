"""Integration smoke tests — these hit the real Venice API.

Run with ``VENICE_API_KEY=... pytest tests/integration -m integration``.
Skipped by default (no key). Keep these tiny; this is a smoke, not a
regression suite.
"""

from __future__ import annotations

import os

import pytest

from veniceresch import AsyncVeniceClient
from veniceresch.types import (
    BillingBalanceResponse,
    ChatCompletionResponse,
    ImageStylesResponse,
    ModelList,
)

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
        assert isinstance(result, ModelList)
        assert isinstance(result.data, list)


async def test_models_list_video(api_key: str) -> None:
    """The ``type`` kwarg is a plain str; any value Venice accepts works end-to-end."""
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.models.list(type="video")
        assert isinstance(result, ModelList)


async def test_billing_balance(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.billing.balance()
        assert isinstance(result, BillingBalanceResponse)


async def test_chat_completion_minimal(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        models = await client.models.list(type="text")
        if not models.data:
            pytest.skip("No text models available on this account.")
        model_id = models.data[0]["id"]
        result = await client.chat.create(
            model=model_id,
            messages=[{"role": "user", "content": "Say 'pong' and nothing else."}],
            max_tokens=10,
        )
        assert isinstance(result, ChatCompletionResponse)
        assert result.choices and result.choices[0]["message"]["content"]


async def test_image_styles(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.image.list_styles()
        assert isinstance(result, ImageStylesResponse)
