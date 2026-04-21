"""``/chat/completions`` resource.

Chat is the API's hot path. Entry points:

* :meth:`AsyncChatResource.create` — non-streaming by default; pass
  ``stream=True`` to get an :class:`~collections.abc.AsyncIterator` of SSE
  events instead. Matches the ``openai`` Python SDK's shape.
* :meth:`AsyncChatResource.stream` — explicit streaming; same underlying
  path, same await contract (``await`` to get the iterator, then
  ``async for`` it).

OpenAI-compatible aliases live on ``client.chat.completions.create(...)``
and ``client.chat.completions.stream(...)`` — they delegate to the same
methods so both namespaces produce identical requests.

Venice's ``/responses`` endpoint lives on its own
:class:`~veniceresch.resources.responses.AsyncResponsesResource` — call it
via ``client.responses.create(...)``.

The most common OpenAI-compatible fields (``temperature``, ``top_p``,
``n``, ``stop``, ``max_tokens``, ``frequency_penalty``,
``presence_penalty``, ``seed``, ``tools``, ``tool_choice``,
``response_format``, ``logprobs``) are named kwargs for IDE
discoverability. Less common Venice- or OpenAI-specific extras
(``reasoning``, ``reasoning_effort``, ``min_p``, ``min_temp``,
``max_temp``, ``top_k``, ``repetition_penalty``, ``prompt_cache_key``,
``top_logprobs``, ``parallel_tool_calls``, ``user``, …) are still
accepted via ``**extra`` and forwarded verbatim. ``venice_parameters``
is passed through as-is.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, cast, overload

import httpx

from veniceresch._errors import translate_httpx_error
from veniceresch.resources._sse import aiter_sse_events, iter_sse_events
from veniceresch.types import ChatCompletionChunk, ChatCompletionResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


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


def _merge_promoted(
    *,
    temperature: float | None,
    top_p: float | None,
    n: int | None,
    stop: str | Sequence[str] | None,
    max_tokens: int | None,
    frequency_penalty: float | None,
    presence_penalty: float | None,
    seed: int | None,
    tools: Sequence[Mapping[str, Any]] | None,
    tool_choice: str | Mapping[str, Any] | None,
    response_format: Mapping[str, Any] | None,
    logprobs: bool | None,
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge promoted named kwargs with ``**extra`` for :func:`_build_body`.

    None values are preserved and filtered by ``_build_body`` itself, so
    callers who pass ``temperature=None`` get the same behavior as callers
    who omit it.
    """
    merged: dict[str, Any] = {
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
        "stop": stop,
        "max_tokens": max_tokens,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "seed": seed,
        "tools": list(tools) if tools is not None else None,
        "tool_choice": tool_choice,
        "response_format": response_format,
        "logprobs": logprobs,
    }
    merged.update(extra)
    return merged


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
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
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
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
        **extra: Any,
    ) -> AsyncIterator[ChatCompletionChunk]: ...

    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
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
        merged = _merge_promoted(
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            seed=seed,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            logprobs=logprobs,
            extra=extra,
        )
        if stream:
            return self._stream_iter(
                model=model,
                messages=messages,
                venice_parameters=venice_parameters,
                extra=merged,
            )
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=merged,
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
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
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
        merged = _merge_promoted(
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            seed=seed,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            logprobs=logprobs,
            extra=extra,
        )
        return self._stream_iter(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=merged,
        )

    async def _stream_iter(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None,
        extra: Mapping[str, Any],
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


class _AsyncCompletionsSubResource:
    """OpenAI-compatible alias: ``client.chat.completions.create(...)``.

    Delegates to :class:`AsyncChatResource` so both spellings produce the
    identical HTTP request and response.
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
        return cast("ChatCompletionResponse | AsyncIterator[ChatCompletionChunk]", result)

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
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
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
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
        **extra: Any,
    ) -> Iterator[ChatCompletionChunk]: ...

    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool = False,
        venice_parameters: Mapping[str, Any] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse | Iterator[ChatCompletionChunk]:
        merged = _merge_promoted(
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            seed=seed,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            logprobs=logprobs,
            extra=extra,
        )
        if stream:
            return self._stream_iter(
                model=model,
                messages=messages,
                venice_parameters=venice_parameters,
                extra=merged,
            )
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=merged,
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
        temperature: float | None = None,
        top_p: float | None = None,
        n: int | None = None,
        stop: str | Sequence[str] | None = None,
        max_tokens: int | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: str | Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        logprobs: bool | None = None,
        **extra: Any,
    ) -> Iterator[ChatCompletionChunk]:
        extra.pop("stream", None)
        merged = _merge_promoted(
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            seed=seed,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            logprobs=logprobs,
            extra=extra,
        )
        return self._stream_iter(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=merged,
        )

    def _stream_iter(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None,
        extra: Mapping[str, Any],
    ) -> Iterator[ChatCompletionChunk]:
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
        return cast("ChatCompletionResponse | Iterator[ChatCompletionChunk]", result)

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
