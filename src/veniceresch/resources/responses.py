"""``/responses`` resource — OpenAI-style Responses API.

Accessed via ``client.responses.create(...)``, matching the ``openai``
Python SDK's top-level namespace. Supports SSE streaming via
:meth:`AsyncResponsesResource.stream` or ``create(stream=True)`` — same
await-then-``async for`` contract as :mod:`veniceresch.resources.chat`.

Venice's swagger documents SSE streaming for this endpoint but does not
define the per-chunk event shape, so :class:`ResponsesChunk` is a
tolerant wrapper — unknown fields land on ``.model_extra``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping
from typing import TYPE_CHECKING, Any, Literal, overload

import httpx

from veniceresch._errors import translate_httpx_error
from veniceresch.resources._sse import aiter_sse_events, iter_sse_events
from veniceresch.types import ResponsesChunk, ResponsesResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


def _build_body(
    *,
    model: str,
    input: Any,
    venice_parameters: Mapping[str, Any] | None,
    extra: Mapping[str, Any],
    stream: bool,
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "input": input}
    if venice_parameters is not None:
        body["venice_parameters"] = dict(venice_parameters)
    if stream:
        body["stream"] = True
    for key, value in extra.items():
        if value is not None:
            body[key] = value
    return body


class AsyncResponsesResource:
    """Async responses resource. Accessed via ``client.responses``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    @overload
    async def create(
        self,
        *,
        model: str,
        input: Any,
        stream: Literal[False] = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse: ...

    @overload
    async def create(
        self,
        *,
        model: str,
        input: Any,
        stream: Literal[True],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[ResponsesChunk]: ...

    async def create(
        self,
        *,
        model: str,
        input: Any,
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse | AsyncIterator[ResponsesChunk]:
        """Call Venice's ``/responses`` endpoint.

        ``stream=False`` (default) returns a :class:`ResponsesResponse`.
        ``stream=True`` returns an async iterator of
        :class:`ResponsesChunk` — ``await`` the call to get the
        iterator, then ``async for`` to consume it::

            stream = await client.responses.create(
                model="m", input="hi", stream=True,
            )
            async for event in stream:
                ...
        """
        if stream:
            return await self.stream(
                model=model,
                input=input,
                venice_parameters=venice_parameters,
                **extra,
            )
        body = _build_body(
            model=model,
            input=input,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=False,
        )
        raw = await self._client._request_json("POST", "/responses", json_body=body)
        return ResponsesResponse.model_construct(**raw)

    async def stream(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[ResponsesChunk]:
        """Stream ``/responses`` output as :class:`ResponsesChunk` events.

        Stops at Venice's ``[DONE]`` sentinel. **Requires ``await`` before
        ``async for``** — same contract as ``create(stream=True)``::

            stream = await client.responses.stream(model="m", input="hi")
            async for event in stream:
                ...
        """
        extra.pop("stream", None)
        return self._stream_iter(
            model=model,
            input=input,
            venice_parameters=venice_parameters,
            **extra,
        )

    async def _stream_iter(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None,
        **extra: Any,
    ) -> AsyncIterator[ResponsesChunk]:
        body = _build_body(
            model=model,
            input=input,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=True,
        )
        async with self._client._request_stream(
            "POST",
            "/responses",
            json_body=body,
            headers={"Accept": "text/event-stream"},
        ) as response:
            try:
                async for event in aiter_sse_events(response.aiter_bytes()):
                    yield ResponsesChunk.model_validate(event)
            except httpx.HTTPError as exc:
                raise translate_httpx_error(exc, "stream POST /responses") from exc


class ResponsesResource:
    """Sync responses resource. Accessed via ``client.responses``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    @overload
    def create(
        self,
        *,
        model: str,
        input: Any,
        stream: Literal[False] = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse: ...

    @overload
    def create(
        self,
        *,
        model: str,
        input: Any,
        stream: Literal[True],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[ResponsesChunk]: ...

    def create(
        self,
        *,
        model: str,
        input: Any,
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse | Iterator[ResponsesChunk]:
        if stream:
            return self.stream(
                model=model,
                input=input,
                venice_parameters=venice_parameters,
                **extra,
            )
        body = _build_body(
            model=model,
            input=input,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=False,
        )
        raw = self._client._request_json("POST", "/responses", json_body=body)
        return ResponsesResponse.model_construct(**raw)

    def stream(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[ResponsesChunk]:
        extra.pop("stream", None)
        body = _build_body(
            model=model,
            input=input,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=True,
        )
        with self._client._request_stream(
            "POST",
            "/responses",
            json_body=body,
            headers={"Accept": "text/event-stream"},
        ) as response:
            try:
                for event in iter_sse_events(response.iter_bytes()):
                    yield ResponsesChunk.model_validate(event)
            except httpx.HTTPError as exc:
                raise translate_httpx_error(exc, "stream POST /responses") from exc


__all__ = ["AsyncResponsesResource", "ResponsesResource"]
