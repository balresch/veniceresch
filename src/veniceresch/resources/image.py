"""``/image/*`` resource.

Covers ``/image/generate`` (JSON by default, raw bytes via
:meth:`AsyncImageResource.generate_binary`), ``/image/edit``,
``/image/multi-edit``, ``/image/upscale``, ``/image/background-remove``
(all of which return raw PNG bytes), and ``/image/styles``.

Image inputs accept :class:`bytes` (raw image data — we base64-encode for you),
:class:`str` (already-encoded base64 or a URL — passed through as-is),
:class:`pathlib.Path` (read and base64-encoded), or a binary file-like object
(read and base64-encoded).

Unlike the multipart audio/augment uploads, these endpoints take base64 in a
JSON body, so the bytes must be fully buffered in memory to encode them — there
is no streaming path here. Pass an ``https://`` URL (or, where supported,
``image_url=``) to avoid uploading large local files at all. On the async
surface the blocking read + base64 of a path / file-like input is offloaded to
a worker thread (see :func:`_encode_image_async`) so the event loop is not
stalled for the duration of the read.
"""

from __future__ import annotations

import asyncio
import base64
import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Literal

from veniceresch.types import GenerateImageResponse, ImageStylesResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


ImageInput = bytes | str | Path | IO[bytes]
ImageFormat = Literal["jpeg", "png", "webp"]
ImageQuality = Literal["low", "medium", "high"]
# A bare image (encoded like any other ImageInput), or a mapping
# ``{"image": ImageInput, "strength": float}`` (strength optional; only models
# with ``supportsStyleReferenceStrength`` honour it).
StyleReference = ImageInput | Mapping[str, Any]

_ENHANCE_DEPRECATION = (
    "image.upscale(enhance=...) is deprecated: Venice removed the enhance / "
    "enhanceCreativity / enhancePrompt / replication fields from /image/upscale. "
    "Use creativity= (0-0.02) instead. enhance= is still forwarded verbatim in "
    "0.7 and will be removed in 1.0."
)


def _encode_image(image: ImageInput) -> str:
    """Normalize an image input to a base64 string (or pass through str/URL).

    ``bytes`` / :class:`~pathlib.Path` / binary file-like objects are
    base64-encoded (buffered in full); a ``str`` is passed through unchanged
    (it is already base64, a data URL, or an ``https://`` URL).
    """
    if isinstance(image, bytes):
        return base64.b64encode(image).decode("ascii")
    if isinstance(image, Path):
        return base64.b64encode(image.read_bytes()).decode("ascii")
    if isinstance(image, str):
        return image  # already base64, a data URL, or an https://... URL
    return base64.b64encode(image.read()).decode("ascii")  # binary file-like


async def _encode_image_async(image: ImageInput) -> str:
    """Async :func:`_encode_image`: offload the blocking read off the loop.

    A ``str`` needs no I/O (passed through) and ``bytes`` are already in memory
    (encoded inline — nothing to offload). Only :class:`~pathlib.Path` /
    file-like inputs do a blocking disk read, so those run the read + base64 in
    a worker thread via :func:`asyncio.to_thread` rather than on the event loop.
    """
    if isinstance(image, (str, bytes)):
        return _encode_image(image)
    return await asyncio.to_thread(_encode_image, image)


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _style_reference(ref: StyleReference, image: str) -> dict[str, Any]:
    if isinstance(ref, Mapping):
        return {**ref, "image": image}
    return {"image": image}


def _style_ref_image(ref: StyleReference) -> ImageInput:
    if isinstance(ref, Mapping):
        if "image" not in ref:
            raise ValueError("style_references mappings need an 'image' key.")
        img: ImageInput = ref["image"]
        return img
    return ref


def _encode_style_refs(refs: Sequence[StyleReference] | None) -> list[dict[str, Any]] | None:
    if refs is None:
        return None
    return [_style_reference(r, _encode_image(_style_ref_image(r))) for r in refs]


async def _encode_style_refs_async(
    refs: Sequence[StyleReference] | None,
) -> list[dict[str, Any]] | None:
    if refs is None:
        return None
    return [_style_reference(r, await _encode_image_async(_style_ref_image(r))) for r in refs]


def _upscale_body(
    image: str, scale: float | None, creativity: float | None, enhance: bool | None, extra: Any
) -> dict[str, Any]:
    if enhance is not None:
        warnings.warn(_ENHANCE_DEPRECATION, DeprecationWarning, stacklevel=3)
    return _drop_none(
        {
            "image": image,
            "scale": scale,
            "creativity": creativity,
            "enhance": enhance,
            **extra,
        }
    )


def _build_generate_body(
    *,
    model: str,
    prompt: str,
    cfg_scale: float | None = None,
    embed_exif_metadata: bool | None = None,
    format: ImageFormat | None = None,
    height: int | None = None,
    hide_watermark: bool | None = None,
    lora_strength: int | None = None,
    negative_prompt: str | None = None,
    variants: int | None = None,
    safe_mode: bool | None = None,
    seed: int | None = None,
    steps: int | None = None,
    style_preset: str | None = None,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    quality: ImageQuality | None = None,
    enable_web_search: bool | None = None,
    width: int | None = None,
    transparent_background: bool | None = None,
    enhance_prompt: bool | None = None,
    disable_prompt_optimization_thinking: bool | None = None,
    style_references: list[dict[str, Any]] | None = None,
    anon_user_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = _drop_none(
        {
            "model": model,
            "prompt": prompt,
            "cfg_scale": cfg_scale,
            "embed_exif_metadata": embed_exif_metadata,
            "format": format,
            "height": height,
            "hide_watermark": hide_watermark,
            "lora_strength": lora_strength,
            "negative_prompt": negative_prompt,
            "variants": variants,
            "safe_mode": safe_mode,
            "seed": seed,
            "steps": steps,
            "style_preset": style_preset,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "quality": quality,
            "enable_web_search": enable_web_search,
            "width": width,
            "transparent_background": transparent_background,
            "enhance_prompt": enhance_prompt,
            "disable_prompt_optimization_thinking": disable_prompt_optimization_thinking,
            "style_references": style_references,
            "anon_user_id": anon_user_id,
        }
    )
    if extra:
        body.update(_drop_none(extra))
    return body


class AsyncImageResource:
    """Async image resource. Accessed via ``client.image``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        cfg_scale: float | None = None,
        embed_exif_metadata: bool | None = None,
        format: ImageFormat | None = None,
        height: int | None = None,
        hide_watermark: bool | None = None,
        lora_strength: int | None = None,
        negative_prompt: str | None = None,
        variants: int | None = None,
        safe_mode: bool | None = None,
        seed: int | None = None,
        steps: int | None = None,
        style_preset: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: ImageQuality | None = None,
        enable_web_search: bool | None = None,
        width: int | None = None,
        transparent_background: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        style_references: Sequence[StyleReference] | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> GenerateImageResponse:
        """Generate an image. Returns :class:`GenerateImageResponse` with
        base64-encoded images in ``result.images``.

        For raw PNG/JPEG bytes, use :meth:`generate_binary`.
        """
        body = _build_generate_body(
            model=model,
            prompt=prompt,
            cfg_scale=cfg_scale,
            embed_exif_metadata=embed_exif_metadata,
            format=format,
            height=height,
            hide_watermark=hide_watermark,
            lora_strength=lora_strength,
            negative_prompt=negative_prompt,
            variants=variants,
            safe_mode=safe_mode,
            seed=seed,
            steps=steps,
            style_preset=style_preset,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            enable_web_search=enable_web_search,
            width=width,
            transparent_background=transparent_background,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            style_references=await _encode_style_refs_async(style_references),
            anon_user_id=anon_user_id,
            extra=extra,
        )
        body.pop("return_binary", None)  # force JSON mode on this method
        raw = await self._client._request_json("POST", "/image/generate", json_body=body)
        return GenerateImageResponse.model_validate(raw)

    async def generate_binary(
        self,
        *,
        model: str,
        prompt: str,
        cfg_scale: float | None = None,
        embed_exif_metadata: bool | None = None,
        format: ImageFormat | None = None,
        height: int | None = None,
        hide_watermark: bool | None = None,
        lora_strength: int | None = None,
        negative_prompt: str | None = None,
        variants: int | None = None,
        safe_mode: bool | None = None,
        seed: int | None = None,
        steps: int | None = None,
        style_preset: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: ImageQuality | None = None,
        enable_web_search: bool | None = None,
        width: int | None = None,
        transparent_background: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        style_references: Sequence[StyleReference] | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> bytes:
        """Generate an image and return raw image bytes (PNG/JPEG/WebP)."""
        body = _build_generate_body(
            model=model,
            prompt=prompt,
            cfg_scale=cfg_scale,
            embed_exif_metadata=embed_exif_metadata,
            format=format,
            height=height,
            hide_watermark=hide_watermark,
            lora_strength=lora_strength,
            negative_prompt=negative_prompt,
            variants=variants,
            safe_mode=safe_mode,
            seed=seed,
            steps=steps,
            style_preset=style_preset,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            enable_web_search=enable_web_search,
            width=width,
            transparent_background=transparent_background,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            style_references=await _encode_style_refs_async(style_references),
            anon_user_id=anon_user_id,
            extra=extra,
        )
        body["return_binary"] = True
        return await self._client._request_bytes("POST", "/image/generate", json_body=body)

    async def edit(
        self,
        *,
        image: ImageInput,
        prompt: str,
        model: str | None = None,
        **extra: Any,
    ) -> bytes:
        """Edit an image with a text prompt. Returns raw PNG bytes."""
        body = _drop_none(
            {
                "image": await _encode_image_async(image),
                "prompt": prompt,
                "model": model,
                **extra,
            }
        )
        return await self._client._request_bytes("POST", "/image/edit", json_body=body)

    async def multi_edit(
        self,
        *,
        images: list[ImageInput],
        prompt: str,
        model_id: str,
        **extra: Any,
    ) -> bytes:
        """Edit up to 3 images together. Returns raw PNG bytes.

        The spec field is ``modelId``; we accept ``model_id`` and translate.
        """
        body = _drop_none(
            {
                "images": [await _encode_image_async(img) for img in images],
                "prompt": prompt,
                "modelId": model_id,
                **extra,
            }
        )
        return await self._client._request_bytes("POST", "/image/multi-edit", json_body=body)

    async def upscale(
        self,
        *,
        image: ImageInput,
        scale: float | None = None,
        creativity: float | None = None,
        enhance: bool | None = None,
        **extra: Any,
    ) -> bytes:
        """Upscale an image. Returns raw PNG bytes.

        ``creativity`` (Venice clamps it to 0-0.02, default 0.01) controls how
        much detail and texture the upscaler adds. ``enhance`` is deprecated —
        Venice dropped it from the endpoint; passing it emits a
        :class:`DeprecationWarning` (it is still forwarded in 0.7).
        """
        body = _upscale_body(await _encode_image_async(image), scale, creativity, enhance, extra)
        return await self._client._request_bytes("POST", "/image/upscale", json_body=body)

    async def background_remove(
        self,
        *,
        image: ImageInput | None = None,
        image_url: str | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> bytes:
        """Remove the background from an image. Returns raw PNG bytes.

        Accepts either ``image=`` (bytes/path/base64) or ``image_url=``.
        """
        if image is None and image_url is None:
            raise ValueError("Must supply either image= or image_url=.")
        body: dict[str, Any] = {}
        if image is not None:
            body["image"] = await _encode_image_async(image)
        if image_url is not None:
            body["image_url"] = image_url
        body.update(_drop_none({"anon_user_id": anon_user_id, **extra}))
        return await self._client._request_bytes("POST", "/image/background-remove", json_body=body)

    async def list_styles(self) -> ImageStylesResponse:
        """List available ``style_preset`` values for :meth:`generate`."""
        raw = await self._client._request_json("GET", "/image/styles")
        return ImageStylesResponse.model_validate(raw)


class ImageResource:
    """Sync image resource. Accessed via ``client.image``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        cfg_scale: float | None = None,
        embed_exif_metadata: bool | None = None,
        format: ImageFormat | None = None,
        height: int | None = None,
        hide_watermark: bool | None = None,
        lora_strength: int | None = None,
        negative_prompt: str | None = None,
        variants: int | None = None,
        safe_mode: bool | None = None,
        seed: int | None = None,
        steps: int | None = None,
        style_preset: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: ImageQuality | None = None,
        enable_web_search: bool | None = None,
        width: int | None = None,
        transparent_background: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        style_references: Sequence[StyleReference] | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> GenerateImageResponse:
        body = _build_generate_body(
            model=model,
            prompt=prompt,
            cfg_scale=cfg_scale,
            embed_exif_metadata=embed_exif_metadata,
            format=format,
            height=height,
            hide_watermark=hide_watermark,
            lora_strength=lora_strength,
            negative_prompt=negative_prompt,
            variants=variants,
            safe_mode=safe_mode,
            seed=seed,
            steps=steps,
            style_preset=style_preset,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            enable_web_search=enable_web_search,
            width=width,
            transparent_background=transparent_background,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            style_references=_encode_style_refs(style_references),
            anon_user_id=anon_user_id,
            extra=extra,
        )
        body.pop("return_binary", None)
        raw = self._client._request_json("POST", "/image/generate", json_body=body)
        return GenerateImageResponse.model_validate(raw)

    def generate_binary(
        self,
        *,
        model: str,
        prompt: str,
        cfg_scale: float | None = None,
        embed_exif_metadata: bool | None = None,
        format: ImageFormat | None = None,
        height: int | None = None,
        hide_watermark: bool | None = None,
        lora_strength: int | None = None,
        negative_prompt: str | None = None,
        variants: int | None = None,
        safe_mode: bool | None = None,
        seed: int | None = None,
        steps: int | None = None,
        style_preset: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: ImageQuality | None = None,
        enable_web_search: bool | None = None,
        width: int | None = None,
        transparent_background: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        style_references: Sequence[StyleReference] | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> bytes:
        body = _build_generate_body(
            model=model,
            prompt=prompt,
            cfg_scale=cfg_scale,
            embed_exif_metadata=embed_exif_metadata,
            format=format,
            height=height,
            hide_watermark=hide_watermark,
            lora_strength=lora_strength,
            negative_prompt=negative_prompt,
            variants=variants,
            safe_mode=safe_mode,
            seed=seed,
            steps=steps,
            style_preset=style_preset,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            enable_web_search=enable_web_search,
            width=width,
            transparent_background=transparent_background,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            style_references=_encode_style_refs(style_references),
            anon_user_id=anon_user_id,
            extra=extra,
        )
        body["return_binary"] = True
        return self._client._request_bytes("POST", "/image/generate", json_body=body)

    def edit(
        self,
        *,
        image: ImageInput,
        prompt: str,
        model: str | None = None,
        **extra: Any,
    ) -> bytes:
        body = _drop_none(
            {
                "image": _encode_image(image),
                "prompt": prompt,
                "model": model,
                **extra,
            }
        )
        return self._client._request_bytes("POST", "/image/edit", json_body=body)

    def multi_edit(
        self,
        *,
        images: list[ImageInput],
        prompt: str,
        model_id: str,
        **extra: Any,
    ) -> bytes:
        body = _drop_none(
            {
                "images": [_encode_image(img) for img in images],
                "prompt": prompt,
                "modelId": model_id,
                **extra,
            }
        )
        return self._client._request_bytes("POST", "/image/multi-edit", json_body=body)

    def upscale(
        self,
        *,
        image: ImageInput,
        scale: float | None = None,
        creativity: float | None = None,
        enhance: bool | None = None,
        **extra: Any,
    ) -> bytes:
        """Sync mirror of :meth:`AsyncImageResource.upscale`."""
        body = _upscale_body(_encode_image(image), scale, creativity, enhance, extra)
        return self._client._request_bytes("POST", "/image/upscale", json_body=body)

    def background_remove(
        self,
        *,
        image: ImageInput | None = None,
        image_url: str | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> bytes:
        if image is None and image_url is None:
            raise ValueError("Must supply either image= or image_url=.")
        body: dict[str, Any] = {}
        if image is not None:
            body["image"] = _encode_image(image)
        if image_url is not None:
            body["image_url"] = image_url
        body.update(_drop_none({"anon_user_id": anon_user_id, **extra}))
        return self._client._request_bytes("POST", "/image/background-remove", json_body=body)

    def list_styles(self) -> ImageStylesResponse:
        raw = self._client._request_json("GET", "/image/styles")
        return ImageStylesResponse.model_validate(raw)


__all__ = [
    "AsyncImageResource",
    "ImageFormat",
    "ImageInput",
    "ImageQuality",
    "ImageResource",
    "StyleReference",
]
