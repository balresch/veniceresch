"""OpenAI-compatible ``/images/generations`` endpoint.

This resource exists solely for drop-in compatibility with the OpenAI
Python SDK's ``client.images.generate(...)`` call. Venice's native image
API — generate, edit, multi-edit, upscale, background-remove, styles —
lives on ``client.image.*`` (singular) and covers a superset of what
this endpoint does.

Venice's ``/images/generations`` accepts the OpenAI parameter set
(``n``, ``size``, ``quality``, ``style``, …). Many of those parameters
are documented as "not used in Venice image generation but supported for
OpenAI compatibility" — they're accepted so callers migrating from the
``openai`` SDK don't have to strip them out. Venice clamps ``n`` to 1
and returns ``VeniceValidationError`` for anything else.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from veniceresch.types import OpenAIImageResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _build_body(
    *,
    prompt: str,
    model: str | None,
    n: int | None,
    size: str | None,
    response_format: str | None,
    quality: str | None,
    style: str | None,
    background: str | None,
    moderation: str | None,
    output_compression: int | None,
    output_format: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    return _drop_none(
        {
            "prompt": prompt,
            "model": model,
            "n": n,
            "size": size,
            "response_format": response_format,
            "quality": quality,
            "style": style,
            "background": background,
            "moderation": moderation,
            "output_compression": output_compression,
            "output_format": output_format,
            **extra,
        }
    )


class AsyncImagesResource:
    """Async OpenAI-compatible images resource. Accessed via ``client.images``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def generate(
        self,
        *,
        prompt: str,
        model: str | None = None,
        n: int | None = None,
        size: str | None = None,
        response_format: str | None = None,
        quality: str | None = None,
        style: str | None = None,
        background: str | None = None,
        moderation: str | None = None,
        output_compression: int | None = None,
        output_format: str | None = None,
        **extra: Any,
    ) -> OpenAIImageResponse:
        """Generate an image via the OpenAI-compatible endpoint.

        Mirrors ``openai.images.generate``. Each entry in
        :attr:`OpenAIImageResponse.data` is ``{"b64_json": "..."}`` or
        ``{"url": "..."}`` depending on ``response_format``.
        """
        body = _build_body(
            prompt=prompt,
            model=model,
            n=n,
            size=size,
            response_format=response_format,
            quality=quality,
            style=style,
            background=background,
            moderation=moderation,
            output_compression=output_compression,
            output_format=output_format,
            extra=extra,
        )
        raw = await self._client._request_json("POST", "/images/generations", json_body=body)
        return OpenAIImageResponse.model_validate(raw)


class ImagesResource:
    """Sync OpenAI-compatible images resource."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def generate(
        self,
        *,
        prompt: str,
        model: str | None = None,
        n: int | None = None,
        size: str | None = None,
        response_format: str | None = None,
        quality: str | None = None,
        style: str | None = None,
        background: str | None = None,
        moderation: str | None = None,
        output_compression: int | None = None,
        output_format: str | None = None,
        **extra: Any,
    ) -> OpenAIImageResponse:
        body = _build_body(
            prompt=prompt,
            model=model,
            n=n,
            size=size,
            response_format=response_format,
            quality=quality,
            style=style,
            background=background,
            moderation=moderation,
            output_compression=output_compression,
            output_format=output_format,
            extra=extra,
        )
        raw = self._client._request_json("POST", "/images/generations", json_body=body)
        return OpenAIImageResponse.model_validate(raw)


__all__ = ["AsyncImagesResource", "ImagesResource"]
