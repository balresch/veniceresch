"""Low-level httpx wrapper — sync and async clients.

Resources import :class:`AsyncVeniceClient` / :class:`VeniceClient` and call
the internal ``_request_json`` / ``_request_bytes`` / ``_request_stream``
helpers. Resources never construct httpx requests directly.

This layer is intentionally small. There is no retry / backoff logic here;
the SDK only raises typed exceptions so callers can dispatch on them and
plug in whatever retry policy they prefer. See ``_errors.py``.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from typing import Any

import httpx
from typing_extensions import Self

from veniceresch._errors import (
    raise_for_response,
    translate_httpx_error,
)
from veniceresch._version import __version__
from veniceresch.resources.audio import AsyncAudioResource, AudioResource
from veniceresch.resources.augment import AsyncAugmentResource, AugmentResource
from veniceresch.resources.billing import AsyncBillingResource, BillingResource
from veniceresch.resources.characters import AsyncCharactersResource, CharactersResource
from veniceresch.resources.chat import AsyncChatResource, ChatResource
from veniceresch.resources.embeddings import AsyncEmbeddingsResource, EmbeddingsResource
from veniceresch.resources.image import AsyncImageResource, ImageResource
from veniceresch.resources.images import AsyncImagesResource, ImagesResource
from veniceresch.resources.models import AsyncModelsResource, ModelsResource
from veniceresch.resources.responses import AsyncResponsesResource, ResponsesResource
from veniceresch.resources.video import AsyncVideoResource, VideoResource

DEFAULT_BASE_URL = "https://api.venice.ai/api/v1"
DEFAULT_TIMEOUT = 60.0
_USER_AGENT = f"veniceresch-python/{__version__}"


def _resolve_api_key(api_key: str | None) -> str:
    key = api_key if api_key is not None else os.environ.get("VENICE_API_KEY")
    if not key:
        raise ValueError("No Venice API key provided. Pass api_key=... or set VENICE_API_KEY.")
    return key


def _has_header(headers: Mapping[str, str] | None, name: str) -> bool:
    if headers is None:
        return False
    target = name.lower()
    return any(k.lower() == target for k in headers)


def _build_headers(
    api_key: str,
    extra: Mapping[str, str] | None,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


class _BaseClient:
    """Shared state between sync and async clients."""

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        timeout: float,
        default_headers: Mapping[str, str] | None,
    ) -> None:
        self._api_key = _resolve_api_key(api_key)
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._default_headers = _build_headers(self._api_key, default_headers)

    @property
    def base_url(self) -> str:
        return self._base_url

    def _merge_headers(self, extra: Mapping[str, str] | None) -> dict[str, str]:
        if not extra:
            return dict(self._default_headers)
        merged = dict(self._default_headers)
        merged.update(extra)
        return merged


class AsyncVeniceClient(_BaseClient):
    """Async client for the Venice.ai API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.AsyncClient | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            default_headers=default_headers,
        )
        if http_client is None:
            self._http = httpx.AsyncClient(timeout=timeout)
            self._owns_http = True
        else:
            self._http = http_client
            self._owns_http = False
        self.chat = AsyncChatResource(self)
        self.responses = AsyncResponsesResource(self)
        self.image = AsyncImageResource(self)
        self.video = AsyncVideoResource(self)
        self.audio = AsyncAudioResource(self)
        self.models = AsyncModelsResource(self)
        self.embeddings = AsyncEmbeddingsResource(self)
        self.billing = AsyncBillingResource(self)
        self.augment = AsyncAugmentResource(self)
        self.characters = AsyncCharactersResource(self)
        self.images = AsyncImagesResource(self)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._send(
            method,
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            files=files,
            data=data,
        )
        parsed = response.json()
        if not isinstance(parsed, dict):
            raise TypeError(
                f"Expected JSON object from {path}, got {type(parsed).__name__}. "
                "Use _request_any for endpoints that return arrays or primitives."
            )
        return parsed

    async def _request_any(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        response = await self._send(
            method,
            path,
            json_body=json_body,
            params=params,
            headers=headers,
        )
        return response.json()

    async def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> bytes:
        response = await self._send(
            method,
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            files=files,
            data=data,
            accept="application/octet-stream",
        )
        return response.content

    @asynccontextmanager
    async def _request_stream(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> AsyncIterator[httpx.Response]:
        """Open a streaming response. Caller iterates the body.

        Errors are raised *before* the context manager yields — so a caller
        that enters the ``async with`` block is guaranteed a 2xx response.
        """
        url = self._url_for(path)
        merged_headers = self._merge_headers(headers)
        try:
            stream_ctx = self._http.stream(
                method,
                url,
                json=json_body,
                params=params,
                headers=merged_headers,
                timeout=self._timeout,
            )
            async with stream_ctx as response:
                if not response.is_success:
                    await response.aread()
                    raise_for_response(response)
                yield response
        except httpx.HTTPError as exc:
            raise translate_httpx_error(exc, f"stream {method} {path}") from exc

    async def _send(
        self,
        method: str,
        path: str,
        *,
        json_body: Any,
        params: Mapping[str, Any] | None,
        headers: Mapping[str, str] | None,
        files: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        accept: str | None = None,
    ) -> httpx.Response:
        url = self._url_for(path)
        merged_headers = self._merge_headers(headers)
        # Caller-provided Accept wins over the default for the request flavor
        # (e.g. video.retrieve_binary passes "video/mp4" explicitly).
        if accept is not None and not _has_header(headers, "accept"):
            merged_headers["Accept"] = accept
        try:
            response = await self._http.request(
                method,
                url,
                json=json_body if files is None else None,
                params=params,
                headers=merged_headers,
                files=files,
                data=data,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise translate_httpx_error(exc, f"{method} {path}") from exc
        if not response.is_success:
            raise_for_response(response)
        return response

    def _url_for(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self._base_url + path


class VeniceClient(_BaseClient):
    """Synchronous client for the Venice.ai API.

    Thin shim over :class:`httpx.Client`. Most callers should prefer
    :class:`AsyncVeniceClient`; this exists for scripts and REPL use.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            default_headers=default_headers,
        )
        if http_client is None:
            self._http = httpx.Client(timeout=timeout)
            self._owns_http = True
        else:
            self._http = http_client
            self._owns_http = False
        self.chat = ChatResource(self)
        self.responses = ResponsesResource(self)
        self.image = ImageResource(self)
        self.video = VideoResource(self)
        self.audio = AudioResource(self)
        self.models = ModelsResource(self)
        self.embeddings = EmbeddingsResource(self)
        self.billing = BillingResource(self)
        self.augment = AugmentResource(self)
        self.characters = CharactersResource(self)
        self.images = ImagesResource(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._send(
            method,
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            files=files,
            data=data,
        )
        parsed = response.json()
        if not isinstance(parsed, dict):
            raise TypeError(
                f"Expected JSON object from {path}, got {type(parsed).__name__}. "
                "Use _request_any for endpoints that return arrays or primitives."
            )
        return parsed

    def _request_any(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        response = self._send(
            method,
            path,
            json_body=json_body,
            params=params,
            headers=headers,
        )
        return response.json()

    def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> bytes:
        response = self._send(
            method,
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            files=files,
            data=data,
            accept="application/octet-stream",
        )
        return response.content

    @contextmanager
    def _request_stream(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Iterator[httpx.Response]:
        url = self._url_for(path)
        merged_headers = self._merge_headers(headers)
        try:
            stream_ctx = self._http.stream(
                method,
                url,
                json=json_body,
                params=params,
                headers=merged_headers,
                timeout=self._timeout,
            )
            with stream_ctx as response:
                if not response.is_success:
                    response.read()
                    raise_for_response(response)
                yield response
        except httpx.HTTPError as exc:
            raise translate_httpx_error(exc, f"stream {method} {path}") from exc

    def _send(
        self,
        method: str,
        path: str,
        *,
        json_body: Any,
        params: Mapping[str, Any] | None,
        headers: Mapping[str, str] | None,
        files: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        accept: str | None = None,
    ) -> httpx.Response:
        url = self._url_for(path)
        merged_headers = self._merge_headers(headers)
        if accept is not None and not _has_header(headers, "accept"):
            merged_headers["Accept"] = accept
        try:
            response = self._http.request(
                method,
                url,
                json=json_body if files is None else None,
                params=params,
                headers=merged_headers,
                files=files,
                data=data,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise translate_httpx_error(exc, f"{method} {path}") from exc
        if not response.is_success:
            raise_for_response(response)
        return response

    def _url_for(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self._base_url + path


__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "AsyncVeniceClient",
    "VeniceClient",
]
