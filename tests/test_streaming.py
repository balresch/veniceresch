"""Tests for ``veniceresch.text_deltas`` (chat-stream text filter)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from contextlib import aclosing

import pytest

from veniceresch import text_deltas
from veniceresch.types import ChatCompletionChunk


def _sse(*events: dict) -> bytes:
    return b"".join(b"data: " + json.dumps(e).encode() + b"\n\n" for e in events) + (
        b"data: [DONE]\n\n"
    )


# A realistic stream: role-only opener, text, a null-content chunk, a
# reasoning-only chunk, a tool-call delta, empty content, more text, a
# finish chunk, and the trailing usage chunk with empty ``choices``.
STREAM = _sse(
    {"id": "c", "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}}]},
    {"id": "c", "choices": [{"index": 0, "delta": {"content": "Hel"}}]},
    {"id": "c", "choices": [{"index": 0, "delta": {"content": None}}]},
    {"id": "c", "choices": [{"index": 0, "delta": {"reasoning_content": "thinking"}}]},
    {
        "id": "c",
        "choices": [
            {"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"name": "f"}}]}}
        ],
    },
    {"id": "c", "choices": [{"index": 0, "delta": {"content": ""}}]},
    {"id": "c", "choices": [{"index": 0, "delta": {"content": "lo"}}]},
    {"id": "c", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
    {"id": "c", "choices": [], "usage": {"total_tokens": 3}},
)

MESSAGES = [{"role": "user", "content": "h"}]


def _mock(mock_api, body: bytes = STREAM):
    return mock_api.post("/chat/completions").respond(
        200, content=body, headers={"content-type": "text/event-stream"}
    )


async def test_async_yields_only_text(mock_api, async_client):
    _mock(mock_api)
    stream = await async_client.chat.stream(model="m", messages=MESSAGES)
    assert [t async for t in text_deltas(stream)] == ["Hel", "lo"]


async def test_async_works_with_create_stream_true(mock_api, async_client):
    _mock(mock_api)
    stream = await async_client.chat.completions.create(model="m", messages=MESSAGES, stream=True)
    assert "".join([t async for t in text_deltas(stream)]) == "Hello"


def test_sync_yields_only_text(mock_api, sync_client):
    _mock(mock_api)
    stream = sync_client.chat.stream(model="m", messages=MESSAGES)
    assert list(text_deltas(stream)) == ["Hel", "lo"]


def test_follows_first_choice_only():
    # n > 1 interleaves choices; only index 0 is followed. A choice without
    # ``index`` counts as the first.
    chunks = [
        ChatCompletionChunk(
            choices=[
                {"index": 1, "delta": {"content": "B"}},
                {"index": 0, "delta": {"content": "A"}},
            ]
        ),
        ChatCompletionChunk(choices=[{"index": 1, "delta": {"content": "B2"}}]),
        ChatCompletionChunk(choices=[{"delta": {"content": "A2"}}]),
        ChatCompletionChunk(choices=[{"index": 0, "delta": None}]),
    ]
    assert list(text_deltas(chunks)) == ["A", "A2"]


async def test_un_awaited_coroutine_raises_helpful_type_error(async_client):
    coro = async_client.chat.stream(model="m", messages=MESSAGES)
    with pytest.raises(TypeError, match="await the call first"):
        text_deltas(coro)  # type: ignore[call-overload]


def test_non_iterable_raises_type_error():
    with pytest.raises(TypeError, match="expects a chat-completion stream"):
        text_deltas(42)  # type: ignore[call-overload]


async def test_closing_async_wrapper_closes_underlying_stream():
    closed = False

    async def source() -> AsyncIterator[ChatCompletionChunk]:
        nonlocal closed
        try:
            for text in ("a", "b", "c"):
                yield ChatCompletionChunk(choices=[{"index": 0, "delta": {"content": text}}])
        finally:
            closed = True

    async with aclosing(text_deltas(source())) as texts:
        async for text in texts:
            assert text == "a"
            break
    assert closed


def test_closing_sync_wrapper_closes_underlying_stream():
    closed = False

    def source() -> Iterator[ChatCompletionChunk]:
        nonlocal closed
        try:
            for text in ("a", "b", "c"):
                yield ChatCompletionChunk(choices=[{"index": 0, "delta": {"content": text}}])
        finally:
            closed = True

    texts = text_deltas(source())
    assert next(texts) == "a"
    texts.close()
    assert closed


async def test_early_break_releases_http_stream(mock_api, async_client):
    # Breaking out and closing the wrapper must not leave the httpx stream
    # half-read: a follow-up request on the same client still works.
    _mock(mock_api)
    stream = await async_client.chat.stream(model="m", messages=MESSAGES)
    async with aclosing(text_deltas(stream)) as texts:
        async for _ in texts:
            break
    _mock(mock_api)
    stream = await async_client.chat.stream(model="m", messages=MESSAGES)
    assert [t async for t in text_deltas(stream)] == ["Hel", "lo"]
