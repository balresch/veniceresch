"""``/chat/completions`` and ``/responses`` resource.

Chat is the API's hot path. The resource exposes three entry points:

* :meth:`AsyncChatResource.create` — non-streaming, returns the parsed JSON body.
* :meth:`AsyncChatResource.stream` — streaming, returns an async iterator over
  SSE events (each already decoded to a dict).
* :meth:`AsyncChatResource.create_response` — Venice's ``/responses`` endpoint.

``venice_parameters`` is passed through as-is. Validation is Venice's job.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any

import httpx

from venice_sdk._errors import translate_httpx_error
from venice_sdk.resources._sse import aiter_sse_events, iter_sse_events

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

    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Create a non-streaming chat completion.

        Any additional OpenAI-compatible fields (``temperature``,
        ``max_tokens``, ``tools``, ...) are forwarded as-is via ``**extra``.
        """
        if extra.get("stream"):
            raise ValueError("Pass stream=True via .stream(...), not .create(stream=True).")
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=False,
        )
        return await self._client._request_json(
            "POST",
            "/chat/completions",
            json_body=body,
        )

    async def stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream a chat completion as SSE events.

        Yields each decoded ``data: {...}`` event until Venice sends ``[DONE]``.
        Errors raise before the first yield, so callers can safely iterate.
        """
        extra.pop("stream", None)
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
                    yield event
            except httpx.HTTPError as exc:
                raise translate_httpx_error(exc, "stream POST /chat/completions") from exc

    async def create_response(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Call Venice's ``/responses`` endpoint (OpenAI-style Responses API)."""
        body: dict[str, Any] = {"model": model, "input": input}
        if venice_parameters is not None:
            body["venice_parameters"] = dict(venice_parameters)
        for key, value in extra.items():
            if value is not None:
                body[key] = value
        return await self._client._request_json(
            "POST",
            "/responses",
            json_body=body,
        )


class ChatResource:
    """Sync chat resource. Accessed via ``client.chat``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        if extra.get("stream"):
            raise ValueError("Pass stream=True via .stream(...), not .create(stream=True).")
        body = _build_body(
            model=model,
            messages=messages,
            venice_parameters=venice_parameters,
            extra=extra,
            stream=False,
        )
        return self._client._request_json(
            "POST",
            "/chat/completions",
            json_body=body,
        )

    def stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[dict[str, Any]]:
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
                yield from iter_sse_events(response.iter_bytes())
            except httpx.HTTPError as exc:
                raise translate_httpx_error(exc, "stream POST /chat/completions") from exc

    def create_response(
        self,
        *,
        model: str,
        input: Any,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"model": model, "input": input}
        if venice_parameters is not None:
            body["venice_parameters"] = dict(venice_parameters)
        for key, value in extra.items():
            if value is not None:
                body[key] = value
        return self._client._request_json(
            "POST",
            "/responses",
            json_body=body,
        )


__all__ = ["AsyncChatResource", "ChatResource"]
