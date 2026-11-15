"""``/image/*`` resource.

Covers ``/image/generate`` (JSON by default, raw bytes via
:meth:`AsyncImageResource.generate_binary`), ``/image/edit``,
``/image/multi-edit``, ``/image/upscale``, ``/image/background-remove``
(all of which return :class:`~veniceresch.types.ImageBytes`: real ``bytes``
plus the ``x-venice-*`` response headers on ``.metadata``), and
``/image/styles``.

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
from urllib.parse import unquote_plus

from veniceresch._content import _parse_json_body
from veniceresch.types import (
    GenerateImageResponse,
    ImageBytes,
    ImageResponseMetadata,
    ImageStylesResponse,
)

if TYPE_CHECKING:
    import httpx

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


def _bool_header(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in ("true", "1"):
        return True
    if lowered in ("false", "0"):
        return False
    return None


def _number_header(value: str | None, kind: type[int] | type[float]) -> Any:
    if value is None:
        return None
    try:
        return kind(value.strip())
    except ValueError:
        return None


def _image_metadata(response: httpx.Response) -> ImageResponseMetadata:
    """Read Venice's ``x-venice-*`` / ``X-Balance-Remaining`` image headers.

    Tolerant by design: a missing or unparseable header becomes ``None`` rather
    than an error, and every ``x-venice-*`` header is kept raw on ``headers``.
    """
    h = response.headers
    enhanced = h.get("x-venice-enhanced-prompt")
    return ImageResponseMetadata(
        is_blurred=_bool_header(h.get("x-venice-is-blurred")),
        is_content_violation=_bool_header(h.get("x-venice-is-content-violation")),
        content_violation_count=_number_header(h.get("x-venice-content-violation-count"), int),
        enhanced_prompt=unquote_plus(enhanced) if enhanced is not None else None,
        model_id=h.get("x-venice-model-id"),
        model_name=h.get("x-venice-model-name"),
        balance_remaining=_number_header(h.get("x-balance-remaining"), float),
        model_deprecation_warning=h.get("x-venice-model-deprecation-warning"),
        model_deprecation_date=h.get("x-venice-model-deprecation-date"),
        deprecated=_bool_header(h.get("x-venice-deprecated")),
        deprecated_replacement=h.get("x-venice-deprecated-replacement"),
        content_type=h.get("content-type"),
        headers={
            name.lower(): value
            for name, value in h.items()
            if name.lower().startswith("x-venice-") or name.lower() == "x-balance-remaining"
        },
    )


def _image_bytes(response: httpx.Response) -> ImageBytes:
    return ImageBytes(response.content, _image_metadata(response))


def _generate_result(response: httpx.Response) -> GenerateImageResponse:
    result = GenerateImageResponse.model_validate(_parse_json_body(response, "/image/generate"))
    result._metadata = _image_metadata(response)
    return result


def _edit_body(
    *,
    image: str,
    prompt: str,
    model: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
    output_format: ImageFormat | None,
    safe_mode: bool | None,
    enhance_prompt: bool | None,
    disable_prompt_optimization_thinking: bool | None,
    transparent_background: bool | None,
    anon_user_id: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    return _drop_none(
        {
            "image": image,
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "output_format": output_format,
            "safe_mode": safe_mode,
            "enhance_prompt": enhance_prompt,
            "disable_prompt_optimization_thinking": disable_prompt_optimization_thinking,
            "transparent_background": transparent_background,
            "anon_user_id": anon_user_id,
            **extra,
        }
    )


def _multi_edit_body(
    *,
    images: list[str],
    prompt: str,
    model_id: str | None,
    model: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
    quality: ImageQuality | None,
    output_format: ImageFormat | None,
    safe_mode: bool | None,
    enhance_prompt: bool | None,
    disable_prompt_optimization_thinking: bool | None,
    transparent_background: bool | None,
    anon_user_id: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    if model_id is not None and model is not None:
        raise ValueError("Pass model= or model_id= to multi_edit, not both (they are aliases).")
    return _drop_none(
        {
            "images": images,
            "prompt": prompt,
            "modelId": model if model is not None else model_id,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "quality": quality,
            "output_format": output_format,
            "safe_mode": safe_mode,
            "enhance_prompt": enhance_prompt,
            "disable_prompt_optimization_thinking": disable_prompt_optimization_thinking,
            "transparent_background": transparent_background,
            "anon_user_id": anon_user_id,
            **extra,
        }
    )


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
        response = await self._client._send(
            "POST", "/image/generate", json_body=body, params=None, headers=None
        )
        return _generate_result(response)

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
    ) -> ImageBytes:
        """Generate an image and return its bytes (PNG/JPEG/WebP).

        Returns :class:`~veniceresch.types.ImageBytes`; header data such as
        ``is_blurred`` is on ``result.metadata``.
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
        body["return_binary"] = True
        return _image_bytes(
            await self._client._request_bytes_response("POST", "/image/generate", json_body=body)
        )

    async def edit(
        self,
        *,
        image: ImageInput,
        prompt: str,
        model: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        output_format: ImageFormat | None = None,
        safe_mode: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        transparent_background: bool | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> ImageBytes:
        """Edit an image with a text prompt. Returns :class:`~veniceresch.types.ImageBytes`.

        ``safe_mode`` defaults to **true** on Venice's side, so NSFW output comes
        back blurred unless you pass ``safe_mode=False``; check
        ``result.metadata.is_blurred``. With ``enhance_prompt=True`` the
        rewritten prompt is on ``result.metadata.enhanced_prompt``. Fields not
        named here can still be passed through ``**extra``.
        """
        body = _edit_body(
            image=await _encode_image_async(image),
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format=output_format,
            safe_mode=safe_mode,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            transparent_background=transparent_background,
            anon_user_id=anon_user_id,
            extra=extra,
        )
        return _image_bytes(
            await self._client._request_bytes_response("POST", "/image/edit", json_body=body)
        )

    async def multi_edit(
        self,
        *,
        images: list[ImageInput],
        prompt: str,
        model_id: str | None = None,
        model: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: ImageQuality | None = None,
        output_format: ImageFormat | None = None,
        safe_mode: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        transparent_background: bool | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> ImageBytes:
        """Edit several images together. Returns :class:`~veniceresch.types.ImageBytes`.

        The maximum number of ``images`` is model-specific: see
        ``model_spec.capabilities.maxInputImages`` from ``models.list()``.
        ``model=`` and ``model_id=`` are aliases (the spec field is ``modelId``);
        pass at most one. Venice defaults to ``firered-image-edit`` when neither
        is given. ``safe_mode`` / ``enhance_prompt`` behave as on :meth:`edit`.
        """
        body = _multi_edit_body(
            images=[await _encode_image_async(img) for img in images],
            prompt=prompt,
            model_id=model_id,
            model=model,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            output_format=output_format,
            safe_mode=safe_mode,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            transparent_background=transparent_background,
            anon_user_id=anon_user_id,
            extra=extra,
        )
        return _image_bytes(
            await self._client._request_bytes_response("POST", "/image/multi-edit", json_body=body)
        )

    async def upscale(
        self,
        *,
        image: ImageInput,
        scale: float | None = None,
        creativity: float | None = None,
        enhance: bool | None = None,
        **extra: Any,
    ) -> ImageBytes:
        """Upscale an image. Returns :class:`~veniceresch.types.ImageBytes`.

        ``creativity`` (Venice clamps it to 0-0.02, default 0.01) controls how
        much detail and texture the upscaler adds. ``enhance`` is deprecated —
        Venice dropped it from the endpoint; passing it emits a
        :class:`DeprecationWarning` (it is still forwarded in 0.7).
        """
        body = _upscale_body(await _encode_image_async(image), scale, creativity, enhance, extra)
        return _image_bytes(
            await self._client._request_bytes_response("POST", "/image/upscale", json_body=body)
        )

    async def background_remove(
        self,
        *,
        image: ImageInput | None = None,
        image_url: str | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> ImageBytes:
        """Remove the background from an image. Returns :class:`~veniceresch.types.ImageBytes`.

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
        return _image_bytes(
            await self._client._request_bytes_response(
                "POST", "/image/background-remove", json_body=body
            )
        )

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
        response = self._client._send(
            "POST", "/image/generate", json_body=body, params=None, headers=None
        )
        return _generate_result(response)

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
    ) -> ImageBytes:
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
        return _image_bytes(
            self._client._request_bytes_response("POST", "/image/generate", json_body=body)
        )

    def edit(
        self,
        *,
        image: ImageInput,
        prompt: str,
        model: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        output_format: ImageFormat | None = None,
        safe_mode: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        transparent_background: bool | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> ImageBytes:
        """Sync mirror of :meth:`AsyncImageResource.edit`."""
        body = _edit_body(
            image=_encode_image(image),
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format=output_format,
            safe_mode=safe_mode,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            transparent_background=transparent_background,
            anon_user_id=anon_user_id,
            extra=extra,
        )
        return _image_bytes(
            self._client._request_bytes_response("POST", "/image/edit", json_body=body)
        )

    def multi_edit(
        self,
        *,
        images: list[ImageInput],
        prompt: str,
        model_id: str | None = None,
        model: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: ImageQuality | None = None,
        output_format: ImageFormat | None = None,
        safe_mode: bool | None = None,
        enhance_prompt: bool | None = None,
        disable_prompt_optimization_thinking: bool | None = None,
        transparent_background: bool | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> ImageBytes:
        """Sync mirror of :meth:`AsyncImageResource.multi_edit`."""
        body = _multi_edit_body(
            images=[_encode_image(img) for img in images],
            prompt=prompt,
            model_id=model_id,
            model=model,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            output_format=output_format,
            safe_mode=safe_mode,
            enhance_prompt=enhance_prompt,
            disable_prompt_optimization_thinking=disable_prompt_optimization_thinking,
            transparent_background=transparent_background,
            anon_user_id=anon_user_id,
            extra=extra,
        )
        return _image_bytes(
            self._client._request_bytes_response("POST", "/image/multi-edit", json_body=body)
        )

    def upscale(
        self,
        *,
        image: ImageInput,
        scale: float | None = None,
        creativity: float | None = None,
        enhance: bool | None = None,
        **extra: Any,
    ) -> ImageBytes:
        """Sync mirror of :meth:`AsyncImageResource.upscale`."""
        body = _upscale_body(_encode_image(image), scale, creativity, enhance, extra)
        return _image_bytes(
            self._client._request_bytes_response("POST", "/image/upscale", json_body=body)
        )

    def background_remove(
        self,
        *,
        image: ImageInput | None = None,
        image_url: str | None = None,
        anon_user_id: str | None = None,
        **extra: Any,
    ) -> ImageBytes:
        if image is None and image_url is None:
            raise ValueError("Must supply either image= or image_url=.")
        body: dict[str, Any] = {}
        if image is not None:
            body["image"] = _encode_image(image)
        if image_url is not None:
            body["image_url"] = image_url
        body.update(_drop_none({"anon_user_id": anon_user_id, **extra}))
        return _image_bytes(
            self._client._request_bytes_response("POST", "/image/background-remove", json_body=body)
        )

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
