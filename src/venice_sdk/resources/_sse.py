"""Minimal SSE (Server-Sent Events) parser for streaming chat responses.

Venice's ``/chat/completions`` with ``stream=true`` returns
``text/event-stream`` with lines like::

    data: {"id": "cmpl-1", "choices": [...]}\\n\\n
    data: {"id": "cmpl-1", "choices": [...]}\\n\\n
    data: [DONE]\\n\\n

We parse chunks line-by-line, emit decoded JSON events, and stop at ``[DONE]``.
This is intentionally tiny — callers that need full SSE semantics (retry,
id/event fields, reconnection) should parse the raw stream themselves.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable, Iterator
from typing import Any

_DONE_SENTINEL = "[DONE]"


def _extract_events(buffer: str) -> tuple[list[str], str]:
    """Split a buffer on SSE event boundaries (blank line = \\n\\n).

    Returns ``(complete_events, remaining_buffer)``.
    """
    # Per the SSE spec, delimiters can be \n\n, \r\r, or \r\n\r\n. Venice
    # sends \n\n in practice, but normalize \r\n to \n so we don't split on
    # the wrong boundary if that ever changes.
    parts = buffer.replace("\r\n", "\n").split("\n\n")
    # The last fragment is incomplete unless buffer ended with \n\n.
    return parts[:-1], parts[-1]


def _parse_event(raw: str) -> Any | None:
    """Turn an SSE event block into a decoded JSON payload, or None to skip.

    Returns ``None`` for non-data lines, comments (``:``), and ``[DONE]``.
    Raising this sentinel lets the caller stop iteration cleanly.
    """
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            # Ignore id:/event:/retry: fields — we don't use them.
            continue
        payload = line[len("data:") :].strip()
        if payload == _DONE_SENTINEL:
            raise _StreamDone
        return json.loads(payload)
    return None


class _StreamDone(Exception):
    """Internal sentinel: SSE stream received [DONE]."""


async def aiter_sse_events(chunks: AsyncIterator[bytes]) -> AsyncIterator[dict[str, Any]]:
    """Async: decode an httpx byte stream into JSON events."""
    buffer = ""
    async for chunk in chunks:
        buffer += chunk.decode("utf-8", errors="replace")
        events, buffer = _extract_events(buffer)
        for raw in events:
            try:
                parsed = _parse_event(raw)
            except _StreamDone:
                return
            if parsed is not None:
                yield parsed
    # Trailing event without a final \n\n (rare but valid).
    if buffer.strip():
        try:
            parsed = _parse_event(buffer)
        except _StreamDone:
            return
        if parsed is not None:
            yield parsed


def iter_sse_events(chunks: Iterable[bytes]) -> Iterator[dict[str, Any]]:
    """Sync: decode an httpx byte stream into JSON events."""
    buffer = ""
    for chunk in chunks:
        buffer += chunk.decode("utf-8", errors="replace")
        events, buffer = _extract_events(buffer)
        for raw in events:
            try:
                parsed = _parse_event(raw)
            except _StreamDone:
                return
            if parsed is not None:
                yield parsed
    if buffer.strip():
        try:
            parsed = _parse_event(buffer)
        except _StreamDone:
            return
        if parsed is not None:
            yield parsed


__all__ = ["aiter_sse_events", "iter_sse_events"]
