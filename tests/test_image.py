"""Tests for the image resource."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
SAMPLE_BYTES = PNG_MAGIC + b"fake-pixels"
SAMPLE_B64 = base64.b64encode(SAMPLE_BYTES).decode("ascii")


# ---- generate -------------------------------------------------------------


async def test_generate_returns_json(mock_api, async_client):
    # Swagger: /image/generate JSON response has images: list[str] (base64).
    route = mock_api.post("/image/generate").respond(200, json={"images": [SAMPLE_B64]})
    result = await async_client.image.generate(
        model="flux-dev",
        prompt="a red cube",
        width=512,
        height=512,
    )
    assert result.images == [SAMPLE_B64]
    body = json.loads(route.calls.last.request.content)
    assert body == {"model": "flux-dev", "prompt": "a red cube", "width": 512, "height": 512}


async def test_generate_drops_return_binary(mock_api, async_client):
    # generate() always goes through the JSON path; a stray return_binary=True
    # would cause Venice to respond with bytes and break the parse.
    route = mock_api.post("/image/generate").respond(200, json={"images": []})
    await async_client.image.generate(
        model="m",
        prompt="p",
        return_binary=True,
    )
    body = json.loads(route.calls.last.request.content)
    assert "return_binary" not in body


async def test_generate_binary_returns_bytes(mock_api, async_client):
    route = mock_api.post("/image/generate").respond(200, content=SAMPLE_BYTES)
    result = await async_client.image.generate_binary(model="m", prompt="p")
    assert result == SAMPLE_BYTES
    body = json.loads(route.calls.last.request.content)
    assert body["return_binary"] is True


# ---- edit ------------------------------------------------------------------


async def test_edit_returns_bytes_and_b64_encodes_input(mock_api, async_client):
    route = mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES)
    result = await async_client.image.edit(
        image=SAMPLE_BYTES,
        prompt="make it blue",
        model="flux-edit",
    )
    assert result == SAMPLE_BYTES
    body = json.loads(route.calls.last.request.content)
    assert body["image"] == SAMPLE_B64  # bytes → base64
    assert body["prompt"] == "make it blue"
    assert body["model"] == "flux-edit"


async def test_edit_passes_string_through(mock_api, async_client):
    # If the caller already has a base64 string or a URL, we don't re-encode.
    route = mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES)
    await async_client.image.edit(image="https://example/img.png", prompt="p")
    body = json.loads(route.calls.last.request.content)
    assert body["image"] == "https://example/img.png"


async def test_edit_reads_from_path(mock_api, async_client, tmp_path: Path):
    img_path = tmp_path / "in.png"
    img_path.write_bytes(SAMPLE_BYTES)
    route = mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES)
    await async_client.image.edit(image=img_path, prompt="p")
    body = json.loads(route.calls.last.request.content)
    assert body["image"] == SAMPLE_B64


# ---- multi_edit ------------------------------------------------------------


async def test_multi_edit_uses_camelcase_modelid(mock_api, async_client):
    route = mock_api.post("/image/multi-edit").respond(200, content=SAMPLE_BYTES)
    result = await async_client.image.multi_edit(
        images=[SAMPLE_BYTES, SAMPLE_BYTES],
        prompt="merge them",
        model_id="flux-multi-edit",
    )
    assert result == SAMPLE_BYTES
    body = json.loads(route.calls.last.request.content)
    # Python-side model_id → API-side modelId (spec uses camelCase here).
    assert body["modelId"] == "flux-multi-edit"
    assert "model_id" not in body
    assert len(body["images"]) == 2
    assert all(isinstance(i, str) for i in body["images"])


# ---- upscale (binary response) --------------------------------------------


async def test_upscale_posts_binary_response(mock_api, async_client):
    route = mock_api.post("/image/upscale").respond(200, content=SAMPLE_BYTES)
    result = await async_client.image.upscale(
        image=SAMPLE_BYTES,
        scale=2.0,
        enhance=True,
    )
    assert result == SAMPLE_BYTES
    body = json.loads(route.calls.last.request.content)
    assert body["scale"] == 2.0
    assert body["enhance"] is True


# ---- background_remove ----------------------------------------------------


async def test_background_remove_with_image(mock_api, async_client):
    mock_api.post("/image/background-remove").respond(200, content=SAMPLE_BYTES)
    result = await async_client.image.background_remove(image=SAMPLE_BYTES)
    assert result == SAMPLE_BYTES


async def test_background_remove_with_url(mock_api, async_client):
    route = mock_api.post("/image/background-remove").respond(200, content=SAMPLE_BYTES)
    await async_client.image.background_remove(image_url="https://x/pic.png")
    body = json.loads(route.calls.last.request.content)
    assert body == {"image_url": "https://x/pic.png"}


async def test_background_remove_requires_input(async_client):
    with pytest.raises(ValueError, match="image"):
        await async_client.image.background_remove()


# ---- list_styles ----------------------------------------------------------


async def test_list_styles(mock_api, async_client):
    mock_api.get("/image/styles").respond(
        200,
        json={"data": ["cinematic", "photographic"], "object": "list"},
    )
    result = await async_client.image.list_styles()
    assert result.data == ["cinematic", "photographic"]
    assert result.object == "list"


# ---- sync ----------------------------------------------------------------


def test_sync_image_edit(mock_api, sync_client):
    mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES)
    result = sync_client.image.edit(image=SAMPLE_BYTES, prompt="p")
    assert result == SAMPLE_BYTES


def test_sync_image_multi_edit(mock_api, sync_client):
    mock_api.post("/image/multi-edit").respond(200, content=SAMPLE_BYTES)
    result = sync_client.image.multi_edit(
        images=[SAMPLE_BYTES],
        prompt="p",
        model_id="m",
    )
    assert result == SAMPLE_BYTES
