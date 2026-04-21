"""Tests for the OpenAI-compatible images resource (``client.images``)."""

from __future__ import annotations

import json

import pytest

from veniceresch import VeniceContentViolationError


async def test_generate_defaults(mock_api, async_client):
    route = mock_api.post("/images/generations").respond(
        200, json={"created": 1700000000, "data": [{"b64_json": "abc"}]}
    )
    result = await async_client.images.generate(prompt="a red cube")
    body = json.loads(route.calls.last.request.content)
    assert body == {"prompt": "a red cube"}
    assert result.created == 1700000000
    assert result.data[0]["b64_json"] == "abc"


async def test_generate_all_openai_params(mock_api, async_client):
    route = mock_api.post("/images/generations").respond(
        200, json={"created": 1, "data": [{"b64_json": "x"}]}
    )
    await async_client.images.generate(
        prompt="p",
        model="venice-image",
        n=1,
        size="1024x1024",
        response_format="b64_json",
        quality="auto",
        style="natural",
        background="auto",
        moderation="auto",
        output_compression=80,
        output_format="png",
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "prompt": "p",
        "model": "venice-image",
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
        "quality": "auto",
        "style": "natural",
        "background": "auto",
        "moderation": "auto",
        "output_compression": 80,
        "output_format": "png",
    }


async def test_generate_drops_none(mock_api, async_client):
    route = mock_api.post("/images/generations").respond(200, json={"created": 1, "data": []})
    await async_client.images.generate(prompt="p", n=None, size=None)
    body = json.loads(route.calls.last.request.content)
    assert body == {"prompt": "p"}


async def test_generate_forwards_extra_kwargs(mock_api, async_client):
    route = mock_api.post("/images/generations").respond(200, json={"created": 1, "data": []})
    await async_client.images.generate(prompt="p", user="customer-1")
    body = json.loads(route.calls.last.request.content)
    assert body["user"] == "customer-1"


async def test_generate_url_response(mock_api, async_client):
    mock_api.post("/images/generations").respond(
        200,
        json={"created": 1, "data": [{"url": "data:image/png;base64,AAAA"}]},
    )
    result = await async_client.images.generate(prompt="p", response_format="url")
    assert result.data[0]["url"].startswith("data:image/png;")


async def test_generate_raises_content_violation(mock_api, async_client):
    mock_api.post("/images/generations").respond(
        400,
        json={"error": "policy", "suggested_prompt": "a tamer red cube"},
    )
    with pytest.raises(VeniceContentViolationError) as info:
        await async_client.images.generate(prompt="something rough")
    assert info.value.suggested_prompt == "a tamer red cube"


def test_sync_generate(mock_api, sync_client):
    mock_api.post("/images/generations").respond(
        200, json={"created": 1, "data": [{"b64_json": "y"}]}
    )
    result = sync_client.images.generate(prompt="p", size="512x512")
    assert result.data[0]["b64_json"] == "y"


def test_images_and_image_coexist(async_client):
    # Sanity: plural + singular namespaces are distinct resources.
    assert async_client.images is not async_client.image
