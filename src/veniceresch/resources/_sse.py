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

    Returns ``None`` for events with no ``data:`` lines (comments ``:``,
    ``id:``/``event:``/``retry:`` only). Raising ``_StreamDone`` lets the caller
    stop iteration cleanly when a ``data:`` line carries ``[DONE]``.

    Per the SSE spec, a single event may contain multiple ``data:`` lines whose
    payloads are joined with ``\\n`` before decoding, so we accumulate every
    ``data:`` line in the block and ``json.loads`` the joined result once. We
    deliberately discard ``event:`` names — Venice's chat and ``/responses``
    streams don't use them semantically today; revisit only if that changes.
    """
    payloads: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            # Ignore id:/event:/retry: fields — we don't use them.
            continue
        payload = line[len("data:") :].strip()
        if payload == _DONE_SENTINEL:
            # Stop the instant we see [DONE]. If a content payload was
            # accumulated earlier in *this same* event block, it is
            # deliberately dropped here. That cannot happen with Venice today:
            # the wire format emits [DONE] in its own event block, one data:
            # line per block (see module docstring). If Venice ever co-locates
            # a final content chunk with [DONE] in one block, decode and yield
            # the accumulated `payloads` here *before* stopping instead of
            # discarding them.
            raise _StreamDone
        payloads.append(payload)
    if not payloads:
        return None
    # Spec-correct: multiple data: lines in one event are ONE logical payload,
    # joined with \n and decoded once. A non-spec server packing two *complete
    # independent* JSON objects into one block as separate data: lines would
    # produce invalid joined JSON ("{...}\n{...}") and raise JSONDecodeError out
    # of the iterator — intentional, matching the "malformed input surfaces"
    # contract (test_invalid_json_raises_cleanly) rather than silently dropping.
    return json.loads("\n".join(payloads))


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
