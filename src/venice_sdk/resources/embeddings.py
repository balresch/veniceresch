"""``/embeddings`` resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from venice_sdk._client import AsyncVeniceClient, VeniceClient


class AsyncEmbeddingsResource:
    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        input: str | Sequence[str],
        model: str,
        **extra: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"input": input, "model": model}
        for k, v in extra.items():
            if v is not None:
                body[k] = v
        return await self._client._request_json("POST", "/embeddings", json_body=body)


class EmbeddingsResource:
    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def create(
        self,
        *,
        input: str | Sequence[str],
        model: str,
        **extra: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"input": input, "model": model}
        for k, v in extra.items():
            if v is not None:
                body[k] = v
        return self._client._request_json("POST", "/embeddings", json_body=body)


__all__ = ["AsyncEmbeddingsResource", "EmbeddingsResource"]
