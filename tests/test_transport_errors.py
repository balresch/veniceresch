"""Transport-layer exception wrapping.

Every httpx call site in ``_client.py`` (and the mid-stream iteration in
``resources/chat.py``) is wrapped so callers get ``VeniceConnectionError`` /
``VeniceTimeoutError`` instead of raw ``httpx.*``. These tests prove it for
all four paths across sync and async, and for mid-stream drops.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest

from veniceresch import (
    AsyncVeniceClient,
    VeniceClient,
    VeniceConnectionError,
    VeniceTimeoutError,
)

# ---- transports that raise on request ------------------------------------


def _raising_async_transport(exc: BaseException) -> httpx.AsyncBaseTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return httpx.MockTransport(handler)


def _raising_sync_transport(exc: BaseException) -> httpx.BaseTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return httpx.MockTransport(handler)


# ---- async _send ----------------------------------------------------------


@pytest.mark.parametrize(
    ("exc", "wrapper"),
    [
        (httpx.ConnectError("dns"), VeniceConnectionError),
        (httpx.ReadTimeout("slow"), VeniceTimeoutError),
        (httpx.WriteTimeout("slow"), VeniceTimeoutError),
        (httpx.PoolTimeout("no slots"), VeniceTimeoutError),
        (httpx.NetworkError("boom"), VeniceConnectionError),
    ],
)
async def test_async_send_wraps_httpx(exc: httpx.HTTPError, wrapper: type) -> None:
    http = httpx.AsyncClient(transport=_raising_async_transport(exc))
    async with AsyncVeniceClient(api_key="k", http_client=http) as client:
        with pytest.raises(wrapper) as info:
            await client.models.list()
        assert isinstance(info.value.__cause__, type(exc))


# ---- sync _send -----------------------------------------------------------


@pytest.mark.parametrize(
    ("exc", "wrapper"),
    [
        (httpx.ConnectError("dns"), VeniceConnectionError),
        (httpx.ReadTimeout("slow"), VeniceTimeoutError),
        (httpx.NetworkError("boom"), VeniceConnectionError),
    ],
)
def test_sync_send_wraps_httpx(exc: httpx.HTTPError, wrapper: type) -> None:
    http = httpx.Client(transport=_raising_sync_transport(exc))
    with VeniceClient(api_key="k", http_client=http) as client:
        with pytest.raises(wrapper) as info:
            client.models.list()
        assert isinstance(info.value.__cause__, type(exc))


# ---- async _request_stream entry ------------------------------------------


async def test_async_stream_entry_wraps_connect_error() -> None:
    http = httpx.AsyncClient(transport=_raising_async_transport(httpx.ConnectError("dns")))
    async with AsyncVeniceClient(api_key="k", http_client=http) as client:
        with pytest.raises(VeniceConnectionError) as info:
            stream = await client.chat.stream(
                model="m", messages=[{"role": "user", "content": "hi"}]
            )
            async for _ in stream:
                pass
        assert isinstance(info.value.__cause__, httpx.ConnectError)


async def test_async_stream_entry_wraps_timeout() -> None:
    http = httpx.AsyncClient(transport=_raising_async_transport(httpx.ReadTimeout("slow")))
    async with AsyncVeniceClient(api_key="k", http_client=http) as client:
        with pytest.raises(VeniceTimeoutError) as info:
            stream = await client.chat.stream(
                model="m", messages=[{"role": "user", "content": "hi"}]
            )
            async for _ in stream:
                pass
        assert isinstance(info.value.__cause__, httpx.ReadTimeout)


# ---- sync _request_stream entry -------------------------------------------


def test_sync_stream_entry_wraps_connect_error() -> None:
    http = httpx.Client(transport=_raising_sync_transport(httpx.ConnectError("dns")))
    with VeniceClient(api_key="k", http_client=http) as client:
        with pytest.raises(VeniceConnectionError) as info:
            for _ in client.chat.stream(model="m", messages=[{"role": "user", "content": "hi"}]):
                pass
        assert isinstance(info.value.__cause__, httpx.ConnectError)


# ---- mid-stream failures --------------------------------------------------


class _AsyncFailingStream(httpx.AsyncByteStream):
    """httpx async stream that yields one chunk then raises."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b'data: {"partial": 1}\n\n'
        raise self._exc


class _SyncFailingStream(httpx.SyncByteStream):
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def __iter__(self) -> Iterator[bytes]:
        yield b'data: {"partial": 1}\n\n'
        raise self._exc


class _AsyncMidStreamFailure(httpx.AsyncBaseTransport):
    """Emits one SSE chunk, then raises on the next read."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=_AsyncFailingStream(self._exc),
        )


class _SyncMidStreamFailure(httpx.BaseTransport):
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=_SyncFailingStream(self._exc),
        )


async def test_async_stream_mid_iteration_wraps_protocol_error() -> None:
    http = httpx.AsyncClient(
        transport=_AsyncMidStreamFailure(httpx.RemoteProtocolError("connection dropped"))
    )
    async with AsyncVeniceClient(api_key="k", http_client=http) as client:
        events: list = []
        with pytest.raises(VeniceConnectionError) as info:
            stream = await client.chat.stream(
                model="m", messages=[{"role": "user", "content": "hi"}]
            )
            async for event in stream:
                events.append(event)
        assert len(events) == 1 and events[0].model_extra == {"partial": 1}
        assert isinstance(info.value.__cause__, httpx.RemoteProtocolError)


def test_sync_stream_mid_iteration_wraps_protocol_error() -> None:
    http = httpx.Client(
        transport=_SyncMidStreamFailure(httpx.RemoteProtocolError("connection dropped"))
    )
    with VeniceClient(api_key="k", http_client=http) as client:
        events: list = []
        with pytest.raises(VeniceConnectionError) as info:
            for event in client.chat.stream(
                model="m", messages=[{"role": "user", "content": "hi"}]
            ):
                events.append(event)
        assert len(events) == 1 and events[0].model_extra == {"partial": 1}
        assert isinstance(info.value.__cause__, httpx.RemoteProtocolError)
