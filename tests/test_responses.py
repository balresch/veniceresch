"""Tests for the responses resource — ``client.responses.create(...)``."""

from __future__ import annotations

import json

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
