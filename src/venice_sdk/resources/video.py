"""``/video/*`` resource.

Venice's video API is queue-based:

1. POST ``/video/queue`` with the generation parameters → receive a ``queue_id``.
2. Poll ``/video/retrieve`` with that ``queue_id`` until ``status == "COMPLETED"``.
3. Either download from the response's ``download_url`` (VPS-backed models) or
   call :meth:`retrieve_binary` to get the MP4 bytes directly.

:meth:`wait_for_completion` wraps steps 2 and 3 and is the only method in this
SDK that does more than "POST and parse."
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from venice_sdk._errors import VeniceAPIError

if TYPE_CHECKING:
    from venice_sdk._client import AsyncVeniceClient, VeniceClient


_STATUS_PROCESSING = "PROCESSING"
_STATUS_COMPLETED = "COMPLETED"
_DEFAULT_TIMEOUT_S = 600.0
_DEFAULT_POLL_S = 2.0


class VeniceVideoTimeoutError(VeniceAPIError):
    """Raised when :meth:`wait_for_completion` exceeds its timeout."""

    def __init__(self, queue_id: str, timeout_s: float) -> None:
        super().__init__(
            f"Video queue_id={queue_id!r} did not complete within {timeout_s:.1f}s",
            status_code=0,
            error_body={"queue_id": queue_id, "timeout_s": timeout_s},
        )
        self.queue_id = queue_id
        self.timeout_s = timeout_s


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class AsyncVideoResource:
    """Async video resource. Accessed via ``client.video``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def queue(
        self,
        *,
        model: str,
        prompt: str,
        duration: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        body = _drop_none({"model": model, "prompt": prompt, "duration": duration, **extra})
        return await self._client._request_json("POST", "/video/queue", json_body=body)

    async def retrieve(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> dict[str, Any]:
        """Poll the queue. Returns a dict with a ``status`` field."""
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        return await self._client._request_json("POST", "/video/retrieve", json_body=body)

    async def retrieve_binary(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> bytes:
        """Return the MP4 bytes for a completed video."""
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        return await self._client._request_bytes(
            "POST",
            "/video/retrieve",
            json_body=body,
            headers={"Accept": "video/mp4"},
        )

    async def quote(
        self,
        *,
        model: str,
        duration: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        body = _drop_none({"model": model, "duration": duration, **extra})
        return await self._client._request_json("POST", "/video/quote", json_body=body)

    async def complete(
        self,
        *,
        model: str,
        queue_id: str,
    ) -> dict[str, Any]:
        body = {"model": model, "queue_id": queue_id}
        return await self._client._request_json("POST", "/video/complete", json_body=body)

    async def transcribe(
        self,
        *,
        url: str,
        response_format: str | None = None,
    ) -> dict[str, Any]:
        body = _drop_none({"url": url, "response_format": response_format})
        return await self._client._request_json(
            "POST",
            "/video/transcriptions",
            json_body=body,
        )

    async def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
    ) -> dict[str, Any]:
        """Poll ``/video/retrieve`` until the job is done.

        Returns the final retrieve response (status ``COMPLETED`` or any
        terminal non-PROCESSING status Venice returns). Raises
        :class:`VeniceVideoTimeoutError` if ``timeout_s`` elapses first.
        """
        deadline = time.monotonic() + timeout_s
        while True:
            result = await self.retrieve(model=model, queue_id=queue_id)
            if result.get("status") != _STATUS_PROCESSING:
                return result
            if time.monotonic() >= deadline:
                raise VeniceVideoTimeoutError(queue_id, timeout_s)
            await asyncio.sleep(poll_interval_s)


class VideoResource:
    """Sync video resource. Accessed via ``client.video``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def queue(
        self,
        *,
        model: str,
        prompt: str,
        duration: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        body = _drop_none({"model": model, "prompt": prompt, "duration": duration, **extra})
        return self._client._request_json("POST", "/video/queue", json_body=body)

    def retrieve(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> dict[str, Any]:
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        return self._client._request_json("POST", "/video/retrieve", json_body=body)

    def retrieve_binary(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> bytes:
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        return self._client._request_bytes(
            "POST",
            "/video/retrieve",
            json_body=body,
            headers={"Accept": "video/mp4"},
        )

    def quote(
        self,
        *,
        model: str,
        duration: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        body = _drop_none({"model": model, "duration": duration, **extra})
        return self._client._request_json("POST", "/video/quote", json_body=body)

    def complete(self, *, model: str, queue_id: str) -> dict[str, Any]:
        body = {"model": model, "queue_id": queue_id}
        return self._client._request_json("POST", "/video/complete", json_body=body)

    def transcribe(self, *, url: str, response_format: str | None = None) -> dict[str, Any]:
        body = _drop_none({"url": url, "response_format": response_format})
        return self._client._request_json("POST", "/video/transcriptions", json_body=body)

    def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        while True:
            result = self.retrieve(model=model, queue_id=queue_id)
            if result.get("status") != _STATUS_PROCESSING:
                return result
            if time.monotonic() >= deadline:
                raise VeniceVideoTimeoutError(queue_id, timeout_s)
            time.sleep(poll_interval_s)


__all__ = [
    "AsyncVideoResource",
    "VeniceVideoTimeoutError",
    "VideoResource",
]
