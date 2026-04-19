"""``/models`` resource: list models, traits, and compatibility mapping.

Venice's ``type`` query parameter accepts ``text``, ``image``, ``embedding``,
``tts``, and ``video`` (among others). The community SDK's ``ModelType``
literal omits ``"video"`` — this resource takes a plain ``str`` so any value
Venice adds later just works without an SDK release.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from venice_sdk._client import AsyncVeniceClient, VeniceClient


class AsyncModelsResource:
    """Async models resource. Accessed via ``client.models``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        type: str | None = None,
    ) -> dict[str, Any]:
        params = {"type": type} if type else None
        return await self._client._request_json("GET", "/models", params=params)

    async def list_traits(self, *, type: str | None = None) -> dict[str, Any]:
        params = {"type": type} if type else None
        return await self._client._request_json("GET", "/models/traits", params=params)

    async def compatibility_mapping(
        self,
        *,
        type: str | None = None,
    ) -> dict[str, Any]:
        params = {"type": type} if type else None
        return await self._client._request_json(
            "GET",
            "/models/compatibility_mapping",
            params=params,
        )


class ModelsResource:
    """Sync models resource."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def list(self, *, type: str | None = None) -> dict[str, Any]:
        params = {"type": type} if type else None
        return self._client._request_json("GET", "/models", params=params)

    def list_traits(self, *, type: str | None = None) -> dict[str, Any]:
        params = {"type": type} if type else None
        return self._client._request_json("GET", "/models/traits", params=params)

    def compatibility_mapping(self, *, type: str | None = None) -> dict[str, Any]:
        params = {"type": type} if type else None
        return self._client._request_json(
            "GET",
            "/models/compatibility_mapping",
            params=params,
        )


__all__ = ["AsyncModelsResource", "ModelsResource"]
