"""Tests for the responses resource — ``client.responses.create(...)``."""

from __future__ import annotations

import json

import pytest

_BODY = {
    "id": "resp-1",
    "object": "response",
    "created_at": 1700000000,
    "status": "completed",
    "model": "m",
    "output": [],
}


async def test_create_posts_to_responses(mock_api, async_client):
    route = mock_api.post("/responses").respond(200, json=_BODY)
    result = await async_client.responses.create(
        model="m",
        input=[{"role": "user", "content": "hi"}],
    )
    assert result.id == "resp-1"
    body = json.loads(route.calls.last.request.content)
    assert body == {"model": "m", "input": [{"role": "user", "content": "hi"}]}


async def test_create_forwards_venice_parameters(mock_api, async_client):
    route = mock_api.post("/responses").respond(200, json=_BODY)
    await async_client.responses.create(
        model="m",
        input="hi",
        venice_parameters={"include_venice_system_prompt": False},
    )
    body = json.loads(route.calls.last.request.content)
    assert body["venice_parameters"] == {"include_venice_system_prompt": False}


async def test_create_drops_none_extras(mock_api, async_client):
    route = mock_api.post("/responses").respond(200, json=_BODY)
    await async_client.responses.create(
        model="m",
        input="hi",
        temperature=None,
    )
    body = json.loads(route.calls.last.request.content)
    assert "temperature" not in body


def test_sync_create(mock_api, sync_client):
    mock_api.post("/responses").respond(200, json=_BODY)
    result = sync_client.responses.create(model="m", input="hi")
    assert result.id == "resp-1"


# ---- streaming ------------------------------------------------------------


async def test_stream_emits_chunks(mock_api, async_client):
    sse_body = (
        b'data: {"id":"resp-1","object":"response","model":"m"}\n\n'
        b'data: {"id":"resp-1","delta":"Hel"}\n\n'
        b'data: {"id":"resp-1","delta":"lo"}\n\n'
        b"data: [DONE]\n\n"
    )
    mock_api.post("/responses").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    stream = await async_client.responses.stream(model="m", input="hi")
    events = [event async for event in stream]
    assert [e.id for e in events] == ["resp-1", "resp-1", "resp-1"]
    # Delta fields aren't known to the ResponsesChunk schema but land in
    # model_extra thanks to extra="allow".
    assert events[1].model_extra == {"delta": "Hel"}
    assert events[2].model_extra == {"delta": "lo"}


async def test_stream_stops_at_done(mock_api, async_client):
    sse_body = b'data: {"id":"a"}\n\ndata: [DONE]\n\ndata: {"id":"after-done"}\n\n'
    mock_api.post("/responses").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    stream = await async_client.responses.stream(model="m", input="hi")
    events = [e async for e in stream]
    assert [e.id for e in events] == ["a"]


async def test_stream_sends_stream_true(mock_api, async_client):
    route = mock_api.post("/responses").respond(
        200,
        content=b"data: [DONE]\n\n",
        headers={"content-type": "text/event-stream"},
    )
    async for _ in await async_client.responses.stream(model="m", input="hi"):
        pass
    body = json.loads(route.calls.last.request.content)
    assert body["stream"] is True


async def test_create_stream_true_returns_iterator(mock_api, async_client):
    sse_body = b'data: {"id":"a"}\n\ndata: {"id":"b"}\n\ndata: [DONE]\n\n'
    mock_api.post("/responses").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    stream = await async_client.responses.create(model="m", input="hi", stream=True)
    events = [e async for e in stream]
    assert [e.id for e in events] == ["a", "b"]


async def test_stream_forwards_venice_parameters(mock_api, async_client):
    route = mock_api.post("/responses").respond(
        200,
        content=b"data: [DONE]\n\n",
        headers={"content-type": "text/event-stream"},
    )
    async for _ in await async_client.responses.stream(
        model="m",
        input="hi",
        venice_parameters={"include_venice_system_prompt": False},
    ):
        pass
    body = json.loads(route.calls.last.request.content)
    assert body["venice_parameters"] == {"include_venice_system_prompt": False}
    assert body["stream"] is True


async def test_stream_raises_error_before_yielding(mock_api, async_client):
    from veniceresch import VeniceRateLimitError

    mock_api.post("/responses").respond(429, json={"error": "slow"})
    with pytest.raises(VeniceRateLimitError):
        stream = await async_client.responses.stream(model="m", input="hi")
        async for _ in stream:
            pass  # pragma: no cover


def test_sync_stream(mock_api, sync_client):
    mock_api.post("/responses").respond(
        200,
        content=b'data: {"id":"s1"}\n\ndata: [DONE]\n\n',
        headers={"content-type": "text/event-stream"},
    )
    events = list(sync_client.responses.stream(model="m", input="hi"))
    assert [e.id for e in events] == ["s1"]


def test_sync_create_stream_true(mock_api, sync_client):
    mock_api.post("/responses").respond(
        200,
        content=b'data: {"id":"s2"}\n\ndata: [DONE]\n\n',
        headers={"content-type": "text/event-stream"},
    )
    events = list(sync_client.responses.create(model="m", input="hi", stream=True))
    assert [e.id for e in events] == ["s2"]
