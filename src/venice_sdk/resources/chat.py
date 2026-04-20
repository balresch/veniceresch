"""``/chat/completions`` and ``/responses`` resource.

Chat is the API's hot path. Entry points:

* :meth:`AsyncChatResource.create` — non-streaming by default; pass
  ``stream=True`` to get an :class:`~collections.abc.AsyncIterator` of SSE
  events instead. Matches the ``openai`` Python SDK's shape.
* :meth:`AsyncChatResource.stream` — explicit streaming; same underlying
  path, same await contract (``await`` to get the iterator, then
  ``async for`` it).
* :meth:`AsyncChatResource.create_response` — Venice's ``/responses``
  endpoint (OpenAI-style Responses API).

OpenAI-compatible aliases live on ``client.chat.completions.create(...)``
and ``client.chat.completions.stream(...)`` — they delegate to the same
methods so both namespaces produce identical requests.

``venice_parameters`` is passed through as-is. Validation is Venice's job.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, cast, overload

import httpx

from venice_sdk._errors import translate_httpx_error
from venice_sdk.resources._sse import aiter_sse_events, iter_sse_events
from venice_sdk.types import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    ResponsesResponse,
)

if TYPE_CHECKING:
    from venice_sdk._client import AsyncVeniceClient, VeniceClient


def _build_body(
    *,
    model: str,
    messages: Sequence[Mapping[str, Any]],
    venice_parameters: Mapping[str, Any] | None,
    extra: Mapping[str, Any],
    stream: bool,
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "messages": list(messages)}
    if venice_parameters is not None:
        body["venice_parameters"] = dict(venice_parameters)
    if stream:
        body["stream"] = True
    for key, value in extra.items():
        if value is not None:
            body[key] = value
    return body


class AsyncChatResource:
    """Async chat resource. Accessed via ``client.chat``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client
        self.completions = _AsyncCompletionsSubResource(self)

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[False] = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse: ...

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[True],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[ChatCompletionChunk]: ...

    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse | AsyncIterator[ChatCompletionChunk]:
        """Create a chat completion.

        ``stream=False`` (default) returns a :class:`ChatCompletionResponse`.
        ``stream=True`` returns an async iterator of
        :class:`ChatCompletionChunk` — ``await`` the call to get the
        iterator, then ``async for`` to consume it::

            stream = await client.chat.create(model="m", messages=[...], stream=True)
            async for chunk in stream:
                ...
        """
        if stream:
            return await self.stream(
                model=model,
                messages=messages,
                venice_parameters=venice_parameters,
                **extra,
            )
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=False,
        )
        raw = await self._client._request_json(
            "POST",
            "/chat/completions",
            json_body=body,
        )
        return ChatCompletionResponse.model_validate(raw)

    async def stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Stream a chat completion as :class:`ChatCompletionChunk` events.

        Stops at Venice's ``[DONE]`` sentinel. **Requires ``await`` before
        ``async for``** — same contract as ``create(stream=True)``::

            stream = await client.chat.stream(model="m", messages=[...])
            async for event in stream:
                ...
        """
        extra.pop("stream", None)
        return self._stream_iter(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            **extra,
        )

    async def _stream_iter(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None,
        **extra: Any,
    ) -> AsyncIterator[ChatCompletionChunk]:
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=True,
        )
        async with self._client._request_stream(
            "POST",
            "/chat/completions",
            json_body=body,
            headers={"Accept": "text/event-stream"},
        ) as response:
            try:
                async for event in aiter_sse_events(response.aiter_bytes()):
                    yield ChatCompletionChunk.model_validate(event)
            except httpx.HTTPError as exc:
                raise translate_httpx_error(exc, "stream POST /chat/completions") from exc

    async def create_response(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse:
        """Call Venice's ``/responses`` endpoint (OpenAI-style Responses API)."""
        body: dict[str, Any] = {"model": model, "input": input}
        if venice_parameters is not None:
            body["venice_parameters"] = dict(venice_parameters)
        for key, value in extra.items():
            if value is not None:
                body[key] = value
        raw = await self._client._request_json(
            "POST",
            "/responses",
            json_body=body,
        )
        return ResponsesResponse.model_construct(**raw)


class _AsyncCompletionsSubResource:
    """OpenAI-compatible alias: ``client.chat.completions.create(...)``.

    Delegates to :class:`AsyncChatResource` so both spellings produce the
    identical HTTP request and response. ``create_response`` is deliberately
    not proxied here — OpenAI's SDK puts the Responses API on a separate
    ``client.responses`` namespace.
    """

    def __init__(self, parent: AsyncChatResource) -> None:
        self._parent = parent

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[False] = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse: ...

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[True],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[ChatCompletionChunk]: ...

    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse | AsyncIterator[ChatCompletionChunk]:
        result = await self._parent.create(
            model=model,
            messages=messages,
            stream=stream,  # type: ignore[call-overload]
            venice_parameters=venice_parameters,
            **extra,
        )
        return cast(
            "ChatCompletionResponse | AsyncIterator[ChatCompletionChunk]", result
        )

    async def stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[ChatCompletionChunk]:
        return await self._parent.stream(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            **extra,
        )


class ChatResource:
    """Sync chat resource. Accessed via ``client.chat``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client
        self.completions = _CompletionsSubResource(self)

    @overload
    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[False] = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse: ...

    @overload
    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[True],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[ChatCompletionChunk]: ...

    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse | Iterator[ChatCompletionChunk]:
        if stream:
            return self.stream(
                model=model,
                messages=messages,
                venice_parameters=venice_parameters,
                **extra,
            )
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=False,
        )
        raw = self._client._request_json(
            "POST",
            "/chat/completions",
            json_body=body,
        )
        return ChatCompletionResponse.model_validate(raw)

    def stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[ChatCompletionChunk]:
        extra.pop("stream", None)
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=True,
        )
        with self._client._request_stream(
            "POST",
            "/chat/completions",
            json_body=body,
            headers={"Accept": "text/event-stream"},
        ) as response:
            try:
                for event in iter_sse_events(response.iter_bytes()):
                    yield ChatCompletionChunk.model_validate(event)
            except httpx.HTTPError as exc:
                raise translate_httpx_error(exc, "stream POST /chat/completions") from exc

    def create_response(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ResponsesResponse:
        body: dict[str, Any] = {"model": model, "input": input}
        if venice_parameters is not None:
            body["venice_parameters"] = dict(venice_parameters)
        for key, value in extra.items():
            if value is not None:
                body[key] = value
        raw = self._client._request_json(
            "POST",
            "/responses",
            json_body=body,
        )
        return ResponsesResponse.model_construct(**raw)


class _CompletionsSubResource:
    """Sync analogue of :class:`_AsyncCompletionsSubResource`."""

    def __init__(self, parent: ChatResource) -> None:
        self._parent = parent

    @overload
    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[False] = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse: ...

    @overload
    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[True],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[ChatCompletionChunk]: ...

    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse | Iterator[ChatCompletionChunk]:
        result = self._parent.create(
            model=model,
            messages=messages,
            stream=stream,  # type: ignore[call-overload]
            venice_parameters=venice_parameters,
            **extra,
        )
        return cast(
            "ChatCompletionResponse | Iterator[ChatCompletionChunk]", result
        )

    def stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[ChatCompletionChunk]:
        return self._parent.stream(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            **extra,
        )


__all__ = ["AsyncChatResource", "ChatResource"]
