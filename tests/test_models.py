"""Tests for the models resource (including the "video" type fix)."""

from __future__ import annotations


async def test_list_no_type(mock_api, async_client):
    route = mock_api.get("/models").respond(200, json={"object": "list", "data": []})
    await async_client.models.list()
    assert route.called
    assert route.calls.last.request.url.query == b""


async def test_list_with_type(mock_api, async_client):
    route = mock_api.get("/models").respond(200, json={"object": "list", "data": []})
    await async_client.models.list(type="text")
    assert route.calls.last.request.url.query == b"type=text"


async def test_list_accepts_video_type(mock_api, async_client):
    # Accept any type string without a release — the ``type`` kwarg is a
    # plain ``str``, not a ``Literal``, so new Venice types just work.
    route = mock_api.get("/models").respond(200, json={"object": "list", "data": []})
    await async_client.models.list(type="video")
    assert b"type=video" in route.calls.last.request.url.query


async def test_list_traits(mock_api, async_client):
    mock_api.get("/models/traits").respond(200, json={"data": {"default": "llama"}})
    result = await async_client.models.list_traits(type="text")
    assert result.data == {"default": "llama"}


async def test_compatibility_mapping(mock_api, async_client):
    mock_api.get("/models/compatibility_mapping").respond(
        200, json={"data": {"gpt-4": "llama-3.3-70b"}}
    )
    result = await async_client.models.compatibility_mapping(type="text")
    assert result.data == {"gpt-4": "llama-3.3-70b"}


def test_sync_models_list(mock_api, sync_client):
    mock_api.get("/models").respond(200, json={"object": "list", "data": [{"id": "m"}]})
    result = sync_client.models.list()
    # .data entries stay as dicts — see ModelList docstring for why.
    assert result.data[0]["id"] == "m"
