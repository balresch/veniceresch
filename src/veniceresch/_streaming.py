"""Convenience helpers over chat-completion streams.

The raw :class:`~veniceresch.types.ChatCompletionChunk` iterator stays the
primary streaming API; :func:`text_deltas` is a thin filter on top of it for
the common "just print the text" case.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, AsyncIterable, Generator, Iterable
from typing import Any, overload

from veniceresch.types import ChatCompletionChunk


def _chunk_text(chunk: ChatCompletionChunk) -> str | None:
    """The first choice's ``delta.content`` if it's a non-empty string."""
    for choice in chunk.choices:
        # Venice / OpenAI streams carry ``index``; with ``n > 1`` the choices
        # interleave, so follow only the first one (index 0 or unlabelled).
        if choice.get("index", 0) != 0:
            continue
        delta = choice.get("delta")
        if not isinstance(delta, dict):
            return None
        content = delta.get("content")
        return content if isinstance(content, str) and content else None
    return None


async def _atext_deltas(
    stream: AsyncIterable[ChatCompletionChunk],
) -> AsyncGenerator[str, None]:
    try:
        async for chunk in stream:
            text = _chunk_text(chunk)
            if text is not None:
                yield text
    finally:
        # Closing this generator (``contextlib.aclosing``, early ``break`` +
        # ``aclose()``) closes the underlying stream too, so the HTTP
        # connection is released instead of waiting for garbage collection.
        aclose = getattr(stream, "aclose", None)
        if aclose is not None:
            await aclose()


def _text_deltas(stream: Iterable[ChatCompletionChunk]) -> Generator[str, None, None]:
    try:
        for chunk in stream:
            text = _chunk_text(chunk)
            if text is not None:
                yield text
    finally:
        close = getattr(stream, "close", None)
        if close is not None:
            close()


@overload
def text_deltas(stream: AsyncIterable[ChatCompletionChunk]) -> AsyncGenerator[str, None]: ...
@overload
def text_deltas(stream: Iterable[ChatCompletionChunk]) -> Generator[str, None, None]: ...
def text_deltas(stream: Any) -> AsyncGenerator[str, None] | Generator[str, None, None]:
    """Yield only the text content from a chat-completion stream.

    Works on both the async iterator from ``await client.chat.stream(...)`` /
    ``await client.chat.create(..., stream=True)`` and the sync iterator from
    :class:`~veniceresch.VeniceClient`::

        stream = await client.chat.stream(model="m", messages=[...])
        async for text in text_deltas(stream):
            print(text, end="", flush=True)

        for text in text_deltas(sync_client.chat.stream(model="m", messages=[...])):
            print(text, end="", flush=True)

    Follows the first choice and skips chunks without text: role-only
    openers, tool-call deltas, ``reasoning_content``, the final usage chunk
    (empty ``choices``), and ``null`` / empty ``content``. Iterate the raw
    chunks when you need any of those.

    Returns a (async) generator; closing it (``close()`` / ``aclose()`` /
    ``contextlib.aclosing``) closes ``stream`` too.
    """
    if inspect.iscoroutine(stream):
        stream.close()  # silence "coroutine was never awaited"
        raise TypeError(
            "text_deltas() got an un-awaited coroutine; await the call first: "
            "text_deltas(await client.chat.stream(...))"
        )
    if isinstance(stream, AsyncIterable):
        return _atext_deltas(stream)
    if isinstance(stream, Iterable):
        return _text_deltas(stream)
    raise TypeError(f"text_deltas() expects a chat-completion stream, got {type(stream).__name__}")


__all__ = ["text_deltas"]
