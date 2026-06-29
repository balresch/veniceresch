"""Unit tests for the low-level SSE parser (``resources/_sse.py``).

These exercise ``aiter_sse_events`` / ``iter_sse_events`` directly against
byte iterators, independent of any resource layer, so parser behavior is pinned
without an HTTP mock.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

import pytest

from veniceresch.resources._sse import aiter_sse_events, iter_sse_events


async def _aiter(chunks: Iterable[bytes]) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


async def _collect_async(chunks: Iterable[bytes]) -> list[dict]:
    return [event async for event in aiter_sse_events(_aiter(chunks))]


def _collect_sync(chunks: Iterable[bytes]) -> list[dict]:
    return list(iter_sse_events(chunks))


# ---- multi-line data: joining (the fix) -----------------------------------


async def test_multiline_data_joins_into_one_json_object():
    # One event, two data: lines. Per the SSE spec they join with \n before
    # decoding — here forming a single JSON object split across lines.
    body = b'data: {"id":\ndata: "multi"}\n\n'
    assert await _collect_async([body]) == [{"id": "multi"}]
    assert _collect_sync([body]) == [{"id": "multi"}]


async def test_done_as_second_data_line_still_stops():
    body = b'data: {"id":"a"}\n\ndata: keep\ndata: [DONE]\n\n'
    # The first event decodes; the second event's [DONE] line stops iteration
    # regardless of the preceding data line in the same block.
    async_events = await _collect_async([b'data: {"id":"a"}\n\n', b"data: [DONE]\n\n"])
    assert async_events == [{"id": "a"}]
    # [DONE] preceded by another data line in the same event also stops cleanly.
    assert _collect_sync([body]) == [{"id": "a"}]


# ---- previously-handled-but-untested cases --------------------------------


async def test_comment_lines_are_ignored():
    body = b': this is a comment\ndata: {"id":"x"}\n\ndata: [DONE]\n\n'
    assert await _collect_async([body]) == [{"id": "x"}]
    assert _collect_sync([body]) == [{"id": "x"}]


async def test_id_and_event_and_retry_fields_are_ignored():
    body = b'id: 1\nevent: message\nretry: 3000\ndata: {"id":"y"}\n\ndata: [DONE]\n\n'
    assert await _collect_async([body]) == [{"id": "y"}]
    assert _collect_sync([body]) == [{"id": "y"}]


async def test_crlf_separators_normalize():
    body = b'data: {"id":"a"}\r\n\r\ndata: {"id":"b"}\r\n\r\ndata: [DONE]\r\n\r\n'
    assert await _collect_async([body]) == [{"id": "a"}, {"id": "b"}]
    assert _collect_sync([body]) == [{"id": "a"}, {"id": "b"}]


async def test_trailing_event_without_final_blank_line():
    # Stream ends right after the last event, no terminating \n\n.
    body = b'data: {"id":"a"}\n\ndata: {"id":"last"}'
    assert await _collect_async([body]) == [{"id": "a"}, {"id": "last"}]
    assert _collect_sync([body]) == [{"id": "a"}, {"id": "last"}]


async def test_done_in_trailing_event_without_blank_line_stops():
    body = b'data: {"id":"a"}\n\ndata: [DONE]'
    assert await _collect_async([body]) == [{"id": "a"}]
    assert _collect_sync([body]) == [{"id": "a"}]


async def test_split_chunks_across_event_boundary():
    # httpx may deliver bytes at arbitrary boundaries — buffering must stitch
    # a JSON object split mid-event back together.
    chunks = [b'data: {"id"', b':"split"}\n', b"\ndata: [DONE]\n\n"]
    assert await _collect_async(chunks) == [{"id": "split"}]
    assert _collect_sync(chunks) == [{"id": "split"}]


async def test_invalid_json_raises_cleanly():
    import json

    body = b"data: {not valid json}\n\n"
    with pytest.raises(json.JSONDecodeError):
        await _collect_async([body])
    with pytest.raises(json.JSONDecodeError):
        _collect_sync([body])


async def test_event_with_only_metadata_yields_nothing():
    body = b"event: ping\nid: 7\n\ndata: [DONE]\n\n"
    assert await _collect_async([body]) == []
    assert _collect_sync([body]) == []


# ---- spec-corner decisions pinned (backlog #11) ---------------------------


async def test_content_payload_colocated_with_done_is_dropped():
    # A content data: line sharing its event block with [DONE] is intentionally
    # discarded (Venice emits [DONE] in its own block, so this can't occur on
    # the real wire — see _parse_event). The earlier {"id":"a"} event is still
    # yielded; the co-located {"id":"dropped"} is not.
    body = b'data: {"id":"a"}\n\ndata: {"id":"dropped"}\ndata: [DONE]\n\n'
    assert await _collect_async([body]) == [{"id": "a"}]
    assert _collect_sync([body]) == [{"id": "a"}]


async def test_multiple_independent_json_objects_in_one_block_raise_cleanly():
    import json

    # Two *complete independent* JSON objects as separate data: lines in one
    # block is non-spec: they join to "{...}\n{...}", which is invalid JSON.
    # We deliberately surface this as JSONDecodeError rather than silently
    # swallowing it (consistent with test_invalid_json_raises_cleanly).
    body = b'data: {"id":"a"}\ndata: {"id":"b"}\n\n'
    with pytest.raises(json.JSONDecodeError):
        await _collect_async([body])
    with pytest.raises(json.JSONDecodeError):
        _collect_sync([body])
