"""``/responses`` resource — OpenAI-style Responses API.

Accessed via ``client.responses.create(...)``, matching the ``openai``
Python SDK's top-level namespace.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from veniceresch.types import ResponsesResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


def _build_body(
    *,
    model: str,
    input: Any,
    venice_parameters: Mapping[str, Any] | None,
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "input": input}
    if venice_parameters is not None:
        body["venice_parameters"] = dict(venice_parameters)
    for key, value in extra.items():
        if value is not None:
            body[key] = value
    return body


class AsyncResponsesResource:
    """Async responses resource. Accessed via ``client.responses``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse:
        """Call Venice's ``/responses`` endpoint (OpenAI-style Responses API)."""
        body = _build_body(
            model=model,
            input=input,
            venice_parameters=venice_parameters,
            extra=extra,
        )
        raw = await self._client._request_json("POST", "/responses", json_body=body)
        return ResponsesResponse.model_construct(**raw)


class ResponsesResource:
    """Sync responses resource. Accessed via ``client.responses``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse:
        body = _build_body(
            model=model,
            input=input,
            venice_parameters=venice_parameters,
            extra=extra,
        )
        raw = self._client._request_json("POST", "/responses", json_body=body)
        return ResponsesResponse.model_construct(**raw)


__all__ = ["AsyncResponsesResource", "ResponsesResource"]
