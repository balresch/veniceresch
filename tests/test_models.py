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


async def test_parsed_data_returns_typed_models(mock_api, async_client):
    mock_api.get("/models").respond(
        200,
        json={
            "object": "list",
            "data": [
                {"id": "llama-3.3-70b", "type": "text", "brand_new_field": "ok"},
                {"id": "venice-image", "type": "image"},
            ],
        },
    )
    result = await async_client.models.list()
    parsed = result.parsed_data()
    assert len(parsed) == 2
    # Attribute access on known fields.
    assert parsed[0].id == "llama-3.3-70b"
    assert parsed[0].type == "text"
    # Unknown fields preserved via extra="allow" (drift-tolerant).
    assert parsed[0].model_extra == {"brand_new_field": "ok"}
    # The raw .data is untouched.
    assert result.data[0]["id"] == "llama-3.3-70b"


async def test_parsed_data_types_image_constraints_and_pricing(mock_api, async_client):
    mock_api.get("/models").respond(
        200,
        json={
            "object": "list",
            "type": "image",
            "data": [
                {
                    "created": 1727966436,
                    "id": "gpt-image-2",
                    "object": "model",
                    "owned_by": "venice.ai",
                    "type": "image",
                    "model_spec": {
                        "privacy": "private",
                        "constraints": {
                            "aspectRatios": ["1:1", "16:9"],
                            "defaultAspectRatio": "1:1",
                            "defaultResolution": "1K",
                            "resolutions": ["1K", "2K", "4K"],
                            "defaultQuality": "high",
                            "qualities": ["low", "medium", "high"],
                            "promptCharacterLimit": 7500,
                            "steps": {"default": 8, "max": 8},
                            "widthHeightDivisor": 8,
                        },
                        "pricing": {
                            "generation": {"usd": 0.01, "diem": 0.01},
                            "resolutions": {
                                "1K": {"usd": 0.27, "diem": 0.27},
                                "2K": {"usd": 0.51, "diem": 0.51},
                            },
                            "quality": {
                                "1K": {
                                    "low": {"usd": 0.02, "diem": 0.02},
                                    "medium": {"usd": 0.07, "diem": 0.07},
                                    "high": {"usd": 0.26, "diem": 0.26},
                                }
                            },
                            "upscale": {
                                "2x": {"usd": 0.02, "diem": 0.02},
                                "4x": {"usd": 0.08, "diem": 0.08},
                            },
                        },
                    },
                }
            ],
        },
    )
    result = await async_client.models.list(type="image")
    model = result.parsed_data()[0]

    assert model.model_spec.constraints.aspectRatios == ["1:1", "16:9"]
    assert model.model_spec.constraints.resolutions == ["1K", "2K", "4K"]
    assert [quality.value for quality in model.model_spec.constraints.qualities] == [
        "low",
        "medium",
        "high",
    ]
    assert model.model_spec.pricing.resolutions["2K"].usd == 0.51
    assert model.model_spec.pricing.quality["1K"].medium.usd == 0.07
