"""``/models`` resource: list models, traits, and compatibility mapping.

Venice's ``type`` query parameter accepts ``text``, ``image``, ``embedding``,
``tts``, ``video`` (and more). This resource takes a plain ``str`` so any
value Venice adds later just works without a client release.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from veniceresch.types import ModelCompatibilityResponse, ModelList, ModelTraitsResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


class AsyncModelsResource:
    """Async models resource. Accessed via ``client.models``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        type: str | None = None,
    ) -> ModelList:
        params = {"type": type} if type else None
        raw = await self._client._request_json("GET", "/models", params=params)
        return ModelList.model_validate(raw)

    async def list_traits(self, *, type: str | None = None) -> ModelTraitsResponse:
        params = {"type": type} if type else None
        raw = await self._client._request_json("GET", "/models/traits", params=params)
        return ModelTraitsResponse.model_validate(raw)

    async def compatibility_mapping(
        self,
        *,
        type: str | None = None,
    ) -> ModelCompatibilityResponse:
        params = {"type": type} if type else None
        raw = await self._client._request_json(
            "GET",
            "/models/compatibility_mapping",
            params=params,
        )
        return ModelCompatibilityResponse.model_validate(raw)


class ModelsResource:
    """Sync models resource."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def list(self, *, type: str | None = None) -> ModelList:
        params = {"type": type} if type else None
        raw = self._client._request_json("GET", "/models", params=params)
        return ModelList.model_validate(raw)

    def list_traits(self, *, type: str | None = None) -> ModelTraitsResponse:
        params = {"type": type} if type else None
        raw = self._client._request_json("GET", "/models/traits", params=params)
        return ModelTraitsResponse.model_validate(raw)

    def compatibility_mapping(self, *, type: str | None = None) -> ModelCompatibilityResponse:
        params = {"type": type} if type else None
        raw = self._client._request_json(
            "GET",
            "/models/compatibility_mapping",
            params=params,
        )
        return ModelCompatibilityResponse.model_validate(raw)


__all__ = ["AsyncModelsResource", "ModelsResource"]
