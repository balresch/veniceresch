"""Tests for the embeddings resource."""

from __future__ import annotations

import json


async def test_create_with_string_input(mock_api, async_client):
    route = mock_api.post("/embeddings").respond(200, json={"data": [{"embedding": [0.1, 0.2]}]})
    await async_client.embeddings.create(input="hello world", model="embed-v1")
    body = json.loads(route.calls.last.request.content)
    assert body == {"input": "hello world", "model": "embed-v1"}


async def test_create_with_list_input(mock_api, async_client):
    route = mock_api.post("/embeddings").respond(200, json={"data": []})
    await async_client.embeddings.create(input=["a", "b"], model="embed-v1")
    body = json.loads(route.calls.last.request.content)
    assert body["input"] == ["a", "b"]


async def test_create_forwards_dimensions(mock_api, async_client):
    route = mock_api.post("/embeddings").respond(200, json={"data": []})
    await async_client.embeddings.create(
        input="h",
        model="m",
        dimensions=512,
        encoding_format="float",
    )
    body = json.loads(route.calls.last.request.content)
    assert body["dimensions"] == 512
    assert body["encoding_format"] == "float"
