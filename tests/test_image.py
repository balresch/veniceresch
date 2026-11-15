"""Tests for the image resource."""

from __future__ import annotations

import base64
import io
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


async def test_generate_forwards_all_official_parameters(mock_api, async_client):
    route = mock_api.post("/image/generate").respond(200, json={"images": []})
    await async_client.image.generate(
        model="gpt-image-2",
        prompt="a red cube",
        cfg_scale=7.5,
        embed_exif_metadata=True,
        format="png",
        height=1024,
        hide_watermark=True,
        lora_strength=50,
        negative_prompt="blurry",
        variants=3,
        safe_mode=False,
        seed=123456789,
        steps=8,
        style_preset="3D Model",
        aspect_ratio="16:9",
        resolution="2K",
        quality="medium",
        enable_web_search=True,
        width=1024,
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "model": "gpt-image-2",
        "prompt": "a red cube",
        "cfg_scale": 7.5,
        "embed_exif_metadata": True,
        "format": "png",
        "height": 1024,
        "hide_watermark": True,
        "lora_strength": 50,
        "negative_prompt": "blurry",
        "variants": 3,
        "safe_mode": False,
        "seed": 123456789,
        "steps": 8,
        "style_preset": "3D Model",
        "aspect_ratio": "16:9",
        "resolution": "2K",
        "quality": "medium",
        "enable_web_search": True,
        "width": 1024,
    }


async def test_generate_binary_returns_bytes(mock_api, async_client):
    route = mock_api.post("/image/generate").respond(200, content=SAMPLE_BYTES)
    result = await async_client.image.generate_binary(model="m", prompt="p")
    assert result == SAMPLE_BYTES
    body = json.loads(route.calls.last.request.content)
    assert body["return_binary"] is True


async def test_generate_binary_forwards_sizing_and_quality(mock_api, async_client):
    route = mock_api.post("/image/generate").respond(200, content=SAMPLE_BYTES)
    await async_client.image.generate_binary(
        model="nano-banana-pro",
        prompt="p",
        aspect_ratio="1:1",
        resolution="4K",
        quality="high",
        format="webp",
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "model": "nano-banana-pro",
        "prompt": "p",
        "format": "webp",
        "aspect_ratio": "1:1",
        "resolution": "4K",
        "quality": "high",
        "return_binary": True,
    }


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


async def test_edit_reads_from_file_like(mock_api, async_client):
    # Base64 endpoints buffer the bytes; a file-like object is read in full.
    route = mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES)
    await async_client.image.edit(image=io.BytesIO(SAMPLE_BYTES), prompt="p")
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
        creativity=0.015,
    )
    assert result == SAMPLE_BYTES
    body = json.loads(route.calls.last.request.content)
    assert body["scale"] == 2.0
    assert body["creativity"] == 0.015
    assert "enhance" not in body


async def test_upscale_enhance_is_deprecated_but_forwarded(mock_api, async_client):
    route = mock_api.post("/image/upscale").respond(200, content=SAMPLE_BYTES)
    with pytest.warns(DeprecationWarning, match="creativity"):
        await async_client.image.upscale(image=SAMPLE_BYTES, enhance=True)
    assert json.loads(route.calls.last.request.content)["enhance"] is True


def test_upscale_enhance_deprecated_sync(mock_api, sync_client):
    mock_api.post("/image/upscale").respond(200, content=SAMPLE_BYTES)
    with pytest.warns(DeprecationWarning):
        sync_client.image.upscale(image=SAMPLE_BYTES, enhance=False)


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


# ---- 0.7.0 generate fields ---------------------------------------------------


async def test_generate_forwards_new_fields_and_encodes_style_references(mock_api, async_client):
    route = mock_api.post("/image/generate").respond(200, json={"images": []})
    await async_client.image.generate(
        model="flux-3",
        prompt="a fox",
        format="png",
        transparent_background=True,
        enhance_prompt=True,
        disable_prompt_optimization_thinking=True,
        anon_user_id="end-user-42",
        style_references=[
            SAMPLE_BYTES,
            {"image": "https://example.com/style.png", "strength": 0.4},
        ],
    )
    body = json.loads(route.calls.last.request.content)
    assert body["transparent_background"] is True
    assert body["enhance_prompt"] is True
    assert body["disable_prompt_optimization_thinking"] is True
    assert body["anon_user_id"] == "end-user-42"
    assert body["style_references"] == [
        {"image": base64.b64encode(SAMPLE_BYTES).decode()},
        {"image": "https://example.com/style.png", "strength": 0.4},
    ]


def test_generate_binary_sync_encodes_style_reference_path(mock_api, sync_client, tmp_path):
    ref = tmp_path / "style.png"
    ref.write_bytes(SAMPLE_BYTES)
    route = mock_api.post("/image/generate").respond(
        200, content=SAMPLE_BYTES, headers={"Content-Type": "image/png"}
    )
    sync_client.image.generate_binary(
        model="flux-3", prompt="a fox", style_references=[{"image": ref, "strength": 1.0}]
    )
    body = json.loads(route.calls.last.request.content)
    assert body["style_references"] == [
        {"image": base64.b64encode(SAMPLE_BYTES).decode(), "strength": 1.0}
    ]
    assert body["return_binary"] is True


def test_style_reference_mapping_requires_image_key(sync_client):
    with pytest.raises(ValueError, match="'image'"):
        sync_client.image.generate(model="m", prompt="p", style_references=[{"strength": 1}])


async def test_background_remove_forwards_anon_user_id(mock_api, async_client):
    route = mock_api.post("/image/background-remove").respond(200, content=SAMPLE_BYTES)
    await async_client.image.background_remove(image_url="https://x/pic.png", anon_user_id="u1")
    assert json.loads(route.calls.last.request.content) == {
        "image_url": "https://x/pic.png",
        "anon_user_id": "u1",
    }


# ---- #12: named EditImageRequest / MultiEditImageRequest fields -----------

_EDIT_FIELDS = dict(
    aspect_ratio="16:9",
    resolution="2K",
    output_format="webp",
    safe_mode=False,
    enhance_prompt=True,
    disable_prompt_optimization_thinking=True,
    transparent_background=False,
    anon_user_id="end-user-1",
)


async def test_edit_forwards_named_fields(mock_api, async_client):
    route = mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES)
    await async_client.image.edit(
        image="https://x/img.png", prompt="p", model="m", **_EDIT_FIELDS, future_field=1
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "image": "https://x/img.png",
        "prompt": "p",
        "model": "m",
        "future_field": 1,
        **_EDIT_FIELDS,
    }


async def test_edit_omits_unset_fields(mock_api, async_client):
    # safe_mode etc. default to None → not sent, so Venice's own defaults apply.
    route = mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES)
    await async_client.image.edit(image="https://x/img.png", prompt="p")
    assert json.loads(route.calls.last.request.content) == {
        "image": "https://x/img.png",
        "prompt": "p",
    }


async def test_multi_edit_forwards_named_fields(mock_api, async_client):
    route = mock_api.post("/image/multi-edit").respond(200, content=SAMPLE_BYTES)
    await async_client.image.multi_edit(
        images=["https://x/a.png", "https://x/b.png"],
        prompt="p",
        model_id="m",
        quality="high",
        **_EDIT_FIELDS,
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "images": ["https://x/a.png", "https://x/b.png"],
        "prompt": "p",
        "modelId": "m",
        "quality": "high",
        **_EDIT_FIELDS,
    }


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [({"model": "m"}, {"modelId": "m"}), ({"model_id": "m"}, {"modelId": "m"}), ({}, {})],
)
def test_multi_edit_model_alias(mock_api, sync_client, kwargs, expected):
    # model_id is now optional (spec default firered-image-edit); model= is an alias.
    route = mock_api.post("/image/multi-edit").respond(200, content=SAMPLE_BYTES)
    sync_client.image.multi_edit(images=["u"], prompt="p", **kwargs)
    assert json.loads(route.calls.last.request.content) == {
        "images": ["u"],
        "prompt": "p",
        **expected,
    }


async def test_multi_edit_rejects_model_and_model_id(mock_api, async_client):
    route = mock_api.post("/image/multi-edit").respond(200, content=SAMPLE_BYTES)
    with pytest.raises(ValueError, match="not both"):
        await async_client.image.multi_edit(images=["u"], prompt="p", model="a", model_id="b")
    assert not route.called


# ---- #13: x-venice-* response headers on ImageBytes.metadata ---------------

_HEADERS = {
    "content-type": "image/png",
    "x-venice-is-blurred": "true",
    "x-venice-is-content-violation": "false",
    "x-venice-enhanced-prompt": "a%20red%20cube%2C+glossy%20%2B%20shiny",
    "x-venice-model-id": "qwen-edit",
    "x-venice-model-name": "Qwen Edit",
    "x-venice-deprecated": "false",
    "X-Balance-Remaining": "12.5",
    "x-unrelated": "ignored",
}


async def test_edit_surfaces_header_metadata(mock_api, async_client):
    from veniceresch.types import ImageBytes

    mock_api.post("/image/edit").respond(200, content=SAMPLE_BYTES, headers=_HEADERS)
    result = await async_client.image.edit(image="u", prompt="p")
    # Still bytes for existing callers.
    assert isinstance(result, bytes) and isinstance(result, ImageBytes)
    assert result == SAMPLE_BYTES
    meta = result.metadata
    assert meta.is_blurred is True
    assert meta.is_content_violation is False
    assert meta.enhanced_prompt == "a red cube, glossy + shiny"
    assert meta.model_id == "qwen-edit"
    assert meta.model_name == "Qwen Edit"
    assert meta.deprecated is False
    assert meta.balance_remaining == 12.5
    assert meta.content_type == "image/png"
    assert meta.content_violation_count is None
    assert meta.headers == {
        "x-venice-is-blurred": "true",
        "x-venice-is-content-violation": "false",
        "x-venice-enhanced-prompt": "a%20red%20cube%2C+glossy%20%2B%20shiny",
        "x-venice-model-id": "qwen-edit",
        "x-venice-model-name": "Qwen Edit",
        "x-venice-deprecated": "false",
        "x-balance-remaining": "12.5",
    }


async def test_metadata_tolerates_missing_and_garbled_headers(mock_api, async_client):
    mock_api.post("/image/edit").respond(
        200,
        content=SAMPLE_BYTES,
        headers={
            "content-type": "image/png",
            "x-venice-is-blurred": "maybe",
            "x-venice-content-violation-count": "lots",
            "X-Balance-Remaining": "n/a",
        },
    )
    meta = (await async_client.image.edit(image="u", prompt="p")).metadata
    assert meta.is_blurred is None
    assert meta.content_violation_count is None
    assert meta.balance_remaining is None
    assert meta.enhanced_prompt is None
    assert meta.headers["x-venice-is-blurred"] == "maybe"


@pytest.mark.parametrize("is_async", [True, False])
@pytest.mark.parametrize(
    ("path", "method", "kwargs"),
    [
        ("/image/generate", "generate_binary", {"model": "m", "prompt": "p"}),
        ("/image/edit", "edit", {"image": "u", "prompt": "p"}),
        ("/image/multi-edit", "multi_edit", {"images": ["u"], "prompt": "p"}),
        ("/image/upscale", "upscale", {"image": "u"}),
        ("/image/background-remove", "background_remove", {"image_url": "u"}),
    ],
)
async def test_all_binary_methods_return_image_bytes(
    mock_api, async_client, sync_client, is_async, path, method, kwargs
):
    from veniceresch.types import ImageBytes

    mock_api.post(path).respond(
        200, content=SAMPLE_BYTES, headers={"content-type": "image/png", "x-venice-is-blurred": "1"}
    )
    client = async_client if is_async else sync_client
    result = getattr(client.image, method)(**kwargs)
    if is_async:
        result = await result
    assert type(result) is ImageBytes
    assert result == SAMPLE_BYTES
    assert result.metadata.is_blurred is True


async def test_generate_json_surfaces_header_metadata(mock_api, async_client):
    mock_api.post("/image/generate").respond(
        200,
        json={"images": [SAMPLE_B64]},
        headers={"x-venice-is-blurred": "true", "x-venice-content-violation-count": "1"},
    )
    result = await async_client.image.generate(model="m", prompt="p")
    assert result.images == [SAMPLE_B64]
    assert result.metadata.is_blurred is True
    assert result.metadata.content_violation_count == 1
    # Header data is not part of the JSON body.
    assert "metadata" not in result.model_dump()


def test_sync_generate_json_surfaces_header_metadata(mock_api, sync_client):
    mock_api.post("/image/generate").respond(
        200, json={"images": []}, headers={"x-venice-enhanced-prompt": "x%20y"}
    )
    assert sync_client.image.generate(model="m", prompt="p").metadata.enhanced_prompt == "x y"


async def test_generate_json_still_maps_errors_and_bad_bodies(mock_api, async_client):
    from veniceresch import VeniceRateLimitError, VeniceUnexpectedContentTypeError

    route = mock_api.post("/image/generate")
    route.respond(429, json={"error": "slow down"})
    with pytest.raises(VeniceRateLimitError):
        await async_client.image.generate(model="m", prompt="p")
    route.respond(200, content=SAMPLE_BYTES, headers={"content-type": "image/png"})
    with pytest.raises(VeniceUnexpectedContentTypeError):
        await async_client.image.generate(model="m", prompt="p")


def test_image_bytes_constructs_and_pickles():
    import copy
    import pickle

    from veniceresch.types import ImageBytes, ImageResponseMetadata

    plain = ImageBytes(b"abc")
    assert plain == b"abc" and plain.metadata == ImageResponseMetadata()
    img = ImageBytes(b"abc", ImageResponseMetadata(is_blurred=True))
    for clone in (pickle.loads(pickle.dumps(img)), copy.deepcopy(img)):
        assert type(clone) is ImageBytes
        assert clone == b"abc" and clone.metadata.is_blurred is True
    # New bytes built from it are plain bytes (documented).
    assert type(img[:1]) is bytes
