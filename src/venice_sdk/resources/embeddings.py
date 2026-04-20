"""``/embeddings`` resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from venice_sdk.types import EmbeddingsResponse

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
    ) -> EmbeddingsResponse:
        body: dict[str, Any] = {"input": input, "model": model}
        for k, v in extra.items():
            if v is not None:
                body[k] = v
        raw = await self._client._request_json("POST", "/embeddings", json_body=body)
        return EmbeddingsResponse.model_validate(raw)


class EmbeddingsResource:
    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def create(
        self,
        *,
        input: str | Sequence[str],
        model: str,
        **extra: Any,
    ) -> EmbeddingsResponse:
        body: dict[str, Any] = {"input": input, "model": model}
        for k, v in extra.items():
            if v is not None:
                body[k] = v
        raw = self._client._request_json("POST", "/embeddings", json_body=body)
        return EmbeddingsResponse.model_validate(raw)


__all__ = ["AsyncEmbeddingsResource", "EmbeddingsResource"]
