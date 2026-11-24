"""Guard the public model-metadata aliases in ``veniceresch.types`` (GH #9).

The generator names ``model_spec.constraints`` / ``.pricing`` variants and some
inline enums positionally (``Constraints1``, ``Pricing4``, ``Type99``). The
public aliases (``TextModelConstraints``, ``InpaintModelPricing``,
``ModelType``, …) bind to those numbered classes, so a regen that reorders or
inserts a variant would silently re-point an alias at a different schema.

These tests pin each alias to the fields that identify it, and check that the
union aliases cover exactly the variants ``ModelSpec`` declares. If one fails
after ``scripts/regen_types.sh``, re-bind the alias in ``types.py`` to the
class that now has these fields (and add an alias for any new variant).
"""

from __future__ import annotations

import types as _pytypes
import typing
from enum import Enum

import pytest

from veniceresch import types as t


def _members(annotation: object) -> set[object]:
    """Union members of a field annotation, without ``None``."""
    args = typing.get_args(annotation)
    if not args:
        return {annotation}
    return {a for a in args if a is not type(None)}


def _fields(model: type) -> set[str]:
    return set(model.model_fields)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("alias", "fields"),
    [
        (
            "ImageModelConstraints",
            {
                "aspectRatios",
                "defaultAspectRatio",
                "defaultQuality",
                "defaultResolution",
                "maxStyleReferences",
                "promptCharacterLimit",
                "qualities",
                "resolutions",
                "steps",
                "supportsStyleReferenceStrength",
                "supportsTransparentBackground",
                "widthHeightDivisor",
            },
        ),
        (
            "TextModelConstraints",
            {"frequency_penalty", "presence_penalty", "repetition_penalty", "temperature", "top_p"},
        ),
        (
            "VideoModelConstraints",
            {
                "aspect_ratios",
                "audio",
                "audio_configurable",
                "durations",
                "hdrResolutions",
                "model_type",
                "per_reference_audio",
                "prompt_character_limit",
                "resolutions",
                "supportsHdr",
                "topaz",
            },
        ),
        (
            "InpaintModelConstraints",
            {
                "aspectRatios",
                "combineImages",
                "defaultQuality",
                "defaultResolution",
                "maxInputImages",
                "promptCharacterLimit",
                "qualities",
                "resolutions",
                "singleImageAspectRatio",
                "supportsTransparentBackground",
            },
        ),
        (
            "TextModelPricing",
            {"cache_input", "cache_write", "cache_write_1h", "extended", "input", "output"},
        ),
        ("ImageModelPricing", {"generation", "quality", "resolutions", "upscale"}),
        ("TtsModelPricing", {"input"}),
        ("AsrModelPricing", {"per_audio_second"}),
        ("InpaintModelPricing", {"inpaint", "inputImages", "quality", "resolutions"}),
        ("MusicGenerationPricing", {"generation"}),
        ("DurationTierPricing", {"durations"}),
        ("MusicPerSecondPricing", {"per_second"}),
        ("PerThousandCharactersPricing", {"per_thousand_characters"}),
        ("VideoModelCapabilities", {"supportsHdr"}),
        ("VideoModelSettings", {"hdrResolutions"}),
    ],
)
def test_alias_points_at_the_right_variant(alias, fields):
    assert _fields(getattr(t, alias)) == fields


def test_tts_and_text_pricing_input_units_differ():
    # TtsModelPricing and TextModelPricing both have ``input``; tell them apart
    # by TextModelPricing's required ``output`` (the field-set test above) and
    # by the TTS one being per *character*, not per token.
    tts_input = t.TtsModelPricing.model_fields["input"].annotation
    assert "character" in (tts_input.model_fields["usd"].description or "")


def test_union_aliases_cover_exactly_the_model_spec_variants():
    spec_fields = t.ModelSpec.model_fields
    assert _members(t.ModelConstraints) == _members(spec_fields["constraints"].annotation)
    assert _members(t.ModelPricing) == _members(spec_fields["pricing"].annotation)


def test_model_spec_and_capabilities_are_what_model_response_uses():
    assert _members(t.ModelResponse.model_fields["model_spec"].annotation) == {t.ModelSpec}
    assert _members(t.ModelSpec.model_fields["capabilities"].annotation) == {t.ModelCapabilities}
    assert "supportsReasoning" in _fields(t.ModelCapabilities)
    # The top-level HDR objects (spec 20261121) took the generator's bare
    # ``Capabilities`` / ``Settings`` names; pin them to ModelResponse too.
    fields = t.ModelResponse.model_fields
    assert _members(fields["capabilities"].annotation) == {t.VideoModelCapabilities}
    assert _members(fields["settings"].annotation) == {t.VideoModelSettings}


def test_model_type_is_the_model_kind_enum():
    assert _members(t.ModelResponse.model_fields["type"].annotation) == {t.ModelType}
    assert issubclass(t.ModelType, Enum)
    assert {"text", "image", "video", "tts", "asr", "inpaint"} <= {m.value for m in t.ModelType}


def test_video_model_type_is_the_video_constraint_enum():
    annotation = t.VideoModelConstraints.model_fields["model_type"].annotation
    assert _members(annotation) == {t.VideoModelType}
    assert {m.value for m in t.VideoModelType} >= {"text-to-video", "image-to-video"}


def test_aliases_are_exported():
    for name in (
        "ModelSpec",
        "ModelCapabilities",
        "ModelType",
        "VideoModelType",
        "ModelConstraints",
        "ModelPricing",
        "TextModelConstraints",
        "InpaintModelPricing",
        "VideoModelCapabilities",
        "VideoModelSettings",
    ):
        assert name in t.__all__
    assert isinstance(t.ModelPricing, _pytypes.UnionType)


def test_parsed_data_narrows_with_public_aliases():
    record = {
        "created": 1727966436,
        "id": "gpt-image-2",
        "object": "model",
        "owned_by": "venice.ai",
        "type": "image",
        "model_spec": {
            "privacy": "private",
            "constraints": {
                "aspectRatios": ["1:1"],
                "promptCharacterLimit": 7500,
                "steps": {"default": 8, "max": 8},
                "widthHeightDivisor": 8,
            },
            "pricing": {
                "generation": {"usd": 0.01, "diem": 0.01},
                "upscale": {"2x": {"usd": 0.02, "diem": 0.02}, "4x": {"usd": 0.08, "diem": 0.08}},
            },
        },
    }
    parsed = t.ModelList(data=[record]).parsed_data()[0]
    assert parsed.type is t.ModelType.image
    spec = parsed.model_spec
    assert spec is not None
    assert isinstance(spec.pricing, t.ImageModelPricing)
    assert isinstance(spec.constraints, t.ImageModelConstraints)


def test_parsed_data_exposes_video_hdr_fields():
    # Shape from spec 20261121: HDR support is published both top-level
    # (capabilities / settings) and on the video constraints.
    record = {
        "created": 1727966436,
        "id": "hdr-video",
        "object": "model",
        "owned_by": "venice.ai",
        "type": "video",
        "capabilities": {"supportsHdr": True},
        "settings": {"hdrResolutions": ["1080p", "4k"]},
        "model_spec": {
            "privacy": "private",
            "constraints": {
                "model_type": "text-to-video",
                "aspect_ratios": ["16:9"],
                "resolutions": ["720p", "1080p", "4k"],
                "durations": ["5s"],
                "audio": False,
                "audio_configurable": False,
                "per_reference_audio": False,
                "supportsHdr": True,
                "hdrResolutions": ["1080p", "4k"],
            },
        },
    }
    parsed = t.ModelList(data=[record]).parsed_data()[0]
    assert isinstance(parsed.capabilities, t.VideoModelCapabilities)
    # ``enum: [true]`` in the spec → a one-member enum, not a bool: truthy, ``.value is True``.
    assert parsed.capabilities.supportsHdr and parsed.capabilities.supportsHdr.value is True
    assert isinstance(parsed.settings, t.VideoModelSettings)
    assert parsed.settings.hdrResolutions == ["1080p", "4k"]
    assert parsed.model_spec is not None
    constraints = parsed.model_spec.constraints
    assert isinstance(constraints, t.VideoModelConstraints)
    assert constraints.supportsHdr is True and constraints.hdrResolutions == ["1080p", "4k"]
