"""``/image/*`` resource.

Covers ``/image/generate`` (JSON by default, raw bytes via
:meth:`AsyncImageResource.generate_binary`), ``/image/edit``,
``/image/multi-edit``, ``/image/upscale``, ``/image/background-remove``
(all of which return raw PNG bytes), and ``/image/styles``.

Image inputs accept :class:`bytes` (raw image data — we base64-encode for you),
:class:`str` (already-encoded base64 or a URL — passed through as-is), or
:class:`pathlib.Path` (read and base64-encoded).
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any

from veniceresch.types import GenerateImageResponse, ImageStylesResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


ImageInput = bytes | str | Path


def _encode_image(image: ImageInput) -> str:
    """Normalize an image input to a base64 string (or pass through str/URL)."""
    if isinstance(image, bytes):
        return base64.b64encode(image).decode("ascii")
    if isinstance(image, Path):
        return base64.b64encode(image.read_bytes()).decode("ascii")
    return image  # str — could be base64, data URL, or https://... URL


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class AsyncImageResource:
    """Async image resource. Accessed via ``client.image``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        **extra: Any,
    ) -> GenerateImageResponse:
        """Generate an image. Returns :class:`GenerateImageResponse` with
        base64-encoded images in ``result.images``.

        For raw PNG/JPEG bytes, use :meth:`generate_binary`.
        """
        body = _drop_none({"model": model, "prompt": prompt, **extra})
        body.pop("return_binary", None)  # force JSON mode on this method
        raw = await self._client._request_json("POST", "/image/generate", json_body=body)
        return GenerateImageResponse.model_validate(raw)

    async def generate_binary(
        self,
        *,
        model: str,
        prompt: str,
        **extra: Any,
    ) -> bytes:
        """Generate an image and return raw image bytes (PNG/JPEG/WebP)."""
        body = _drop_none({"model": model, "prompt": prompt, **extra})
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
                "image": _encode_image(image),
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
                "images": [_encode_image(img) for img in images],
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
        enhance: bool | None = None,
        **extra: Any,
    ) -> bytes:
        """Upscale an image. Returns raw PNG bytes."""
        body = _drop_none(
            {
                "image": _encode_image(image),
                "scale": scale,
                "enhance": enhance,
                **extra,
            }
        )
        return await self._client._request_bytes("POST", "/image/upscale", json_body=body)

    async def background_remove(
        self,
        *,
        image: ImageInput | None = None,
        image_url: str | None = None,
    ) -> bytes:
        """Remove the background from an image. Returns raw PNG bytes.

        Accepts either ``image=`` (bytes/path/base64) or ``image_url=``.
        """
        if image is None and image_url is None:
            raise ValueError("Must supply either image= or image_url=.")
        body: dict[str, Any] = {}
        if image is not None:
            body["image"] = _encode_image(image)
        if image_url is not None:
            body["image_url"] = image_url
        return await self._client._request_bytes("POST", "/image/background-remove", json_body=body)

    async def list_styles(self) -> ImageStylesResponse:
        """List available ``style_preset`` values for :meth:`generate`."""
        raw = await self._client._request_json("GET", "/image/styles")
        return ImageStylesResponse.model_validate(raw)


class ImageResource:
    """Sync image resource. Accessed via ``client.image``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def generate(self, *, model: str, prompt: str, **extra: Any) -> GenerateImageResponse:
        body = _drop_none({"model": model, "prompt": prompt, **extra})
        body.pop("return_binary", None)
        raw = self._client._request_json("POST", "/image/generate", json_body=body)
        return GenerateImageResponse.model_validate(raw)

    def generate_binary(self, *, model: str, prompt: str, **extra: Any) -> bytes:
        body = _drop_none({"model": model, "prompt": prompt, **extra})
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
        enhance: bool | None = None,
        **extra: Any,
    ) -> bytes:
        body = _drop_none(
            {
                "image": _encode_image(image),
                "scale": scale,
                "enhance": enhance,
                **extra,
            }
        )
        return self._client._request_bytes("POST", "/image/upscale", json_body=body)

    def background_remove(
        self,
        *,
        image: ImageInput | None = None,
        image_url: str | None = None,
    ) -> bytes:
        if image is None and image_url is None:
            raise ValueError("Must supply either image= or image_url=.")
        body: dict[str, Any] = {}
        if image is not None:
            body["image"] = _encode_image(image)
        if image_url is not None:
            body["image_url"] = image_url
        return self._client._request_bytes("POST", "/image/background-remove", json_body=body)

    def list_styles(self) -> ImageStylesResponse:
        raw = self._client._request_json("GET", "/image/styles")
        return ImageStylesResponse.model_validate(raw)


__all__ = ["AsyncImageResource", "ImageInput", "ImageResource"]
