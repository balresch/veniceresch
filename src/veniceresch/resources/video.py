"""``/video/*`` resource.

Venice's video API is queue-based:

1. POST ``/video/queue`` with the generation parameters → receive a ``queue_id``.
2. Poll ``/video/retrieve`` with that ``queue_id`` until ``status == "COMPLETED"``.
3. Fetch the MP4 bytes with :meth:`download`.

The two model families return the media differently: direct-bytes models hand
back MP4 bytes from ``/video/retrieve`` (what :meth:`retrieve_binary` reads),
while VPS-backed models (the ``-private`` grok models) ignore ``Accept:
video/mp4`` and answer with a JSON status object. For those models the media
URL is *not* on the retrieve body — it is the ``download_url`` returned on the
``video.queue()`` submit response (:attr:`~veniceresch.types.VideoQueueResponse.download_url`);
``/video/retrieve`` is for status polling only. :meth:`retrieve_binary` raises
:class:`~veniceresch._errors.VeniceUnexpectedContentTypeError` rather than
returning that JSON as bogus "bytes". :meth:`download` handles both families:
pass the queue submit's ``download_url`` for VPS-backed models, or let it fall
back to ``retrieve_binary`` for direct-bytes models.

:meth:`wait_for_completion` wraps the polling loop (step 2) and is the only
method in this SDK that does more than "POST and parse."
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from veniceresch._errors import VeniceAPIError, VeniceUnexpectedContentTypeError
from veniceresch.types import (
    VideoCompleteResponse,
    VideoQueueResponse,
    VideoQuoteResponse,
    VideoRetrieveResponse,
    VideoTranscriptionResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


_STATUS_PROCESSING = "PROCESSING"
_DEFAULT_TIMEOUT_S = 600.0
_DEFAULT_POLL_S = 2.0
# Venice does not document failure status strings for /video/retrieve (the
# swagger enum is PROCESSING/COMPLETED only). This curated, case-insensitive
# set is what ``wait_for_completion(raise_on_failed=True)`` treats as failure;
# any other non-PROCESSING status (including unknown ones) still returns
# normally, preserving the "tolerate unknown terminal statuses" contract.
_FAILURE_STATUSES = frozenset({"FAILED", "CANCELLED", "CANCELED", "ERROR"})


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


class VeniceVideoFailedError(VeniceAPIError):
    """Raised by :meth:`wait_for_completion` with ``raise_on_failed=True`` when
    the job reaches a known failure terminal state (see ``_FAILURE_STATUSES``).

    The final retrieve response is on :attr:`result` for inspection.
    """

    def __init__(self, queue_id: str, status: str, result: VideoRetrieveResponse) -> None:
        super().__init__(
            f"Video queue_id={queue_id!r} ended in failure status {status!r}",
            status_code=0,
            error_body={"queue_id": queue_id, "status": status},
        )
        self.queue_id = queue_id
        self.status = status
        self.result = result


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _download_url_from(exc: VeniceUnexpectedContentTypeError) -> str | None:
    """Pull a non-empty ``download_url`` out of a JSON retrieve body, if any."""
    body = exc.error_body
    if isinstance(body, dict):
        url = body.get("download_url")
        if isinstance(url, str) and url:
            return url
    return None


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
    ) -> VideoQueueResponse:
        body = _drop_none({"model": model, "prompt": prompt, "duration": duration, **extra})
        raw = await self._client._request_json("POST", "/video/queue", json_body=body)
        return VideoQueueResponse.model_validate(raw)

    async def retrieve(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> VideoRetrieveResponse:
        """Poll the queue. Returns a model with a ``status`` field."""
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        raw = await self._client._request_json("POST", "/video/retrieve", json_body=body)
        return VideoRetrieveResponse.model_validate(raw)

    async def retrieve_binary(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> bytes:
        """Return the MP4 bytes straight from ``/video/retrieve``.

        Works for direct-bytes models. VPS-backed models answer this call with
        a JSON status object instead of MP4 bytes, so this raises
        :class:`~veniceresch._errors.VeniceUnexpectedContentTypeError` for them
        (the parsed JSON status body is on the error's ``error_body``; it does
        not carry the media URL — that is on the ``video.queue()`` submit
        response). Prefer :meth:`download`, which handles both families.
        """
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

    async def download(
        self,
        *,
        model: str,
        queue_id: str,
        download_url: str | None = None,
    ) -> bytes:
        """Return the MP4 bytes for a completed video, for any model family.

        If ``download_url`` is given — the value from the ``video.queue()``
        submit response (:attr:`~veniceresch.types.VideoQueueResponse.download_url`),
        which is the only handle to the media for VPS-backed ``-private`` models
        — the media is fetched directly from it (presigned URL, auth stripped).

        Otherwise tries :meth:`retrieve_binary` first (one call for direct-bytes
        models). If Venice answers with JSON instead, any ``download_url`` in
        that body is fetched directly; otherwise
        :class:`~veniceresch._errors.VeniceUnexpectedContentTypeError` is raised
        (VPS-backed models do not carry the URL on ``/video/retrieve`` — capture
        it from ``queue()`` and pass it here).
        """
        if download_url is not None:
            return await self._client._request_bytes("GET", download_url, no_auth=True)
        try:
            return await self.retrieve_binary(model=model, queue_id=queue_id)
        except VeniceUnexpectedContentTypeError as exc:
            url = _download_url_from(exc)
            if url is None:
                raise
            return await self._client._request_bytes("GET", url, no_auth=True)

    async def quote(
        self,
        *,
        model: str,
        duration: str | None = None,
        **extra: Any,
    ) -> VideoQuoteResponse:
        body = _drop_none({"model": model, "duration": duration, **extra})
        raw = await self._client._request_json("POST", "/video/quote", json_body=body)
        return VideoQuoteResponse.model_validate(raw)

    async def complete(
        self,
        *,
        model: str,
        queue_id: str,
    ) -> VideoCompleteResponse:
        body = {"model": model, "queue_id": queue_id}
        raw = await self._client._request_json("POST", "/video/complete", json_body=body)
        return VideoCompleteResponse.model_validate(raw)

    async def transcribe(
        self,
        *,
        url: str,
        response_format: str | None = None,
    ) -> VideoTranscriptionResponse:
        body = _drop_none({"url": url, "response_format": response_format})
        raw = await self._client._request_json(
            "POST",
            "/video/transcriptions",
            json_body=body,
        )
        return VideoTranscriptionResponse.model_validate(raw)

    async def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
        raise_on_failed: bool = False,
    ) -> VideoRetrieveResponse:
        """Poll ``/video/retrieve`` until the job reaches a *terminal* state.

        Waits for a terminal state, not necessarily a *successful* one: by
        default it returns the final retrieve response for any non-PROCESSING
        status (``COMPLETED`` or any other terminal status Venice returns),
        which preserves tolerance of undocumented terminal statuses. Raises
        :class:`VeniceVideoTimeoutError` if ``timeout_s`` elapses first.

        Pass ``raise_on_failed=True`` to instead raise
        :class:`VeniceVideoFailedError` on a known failure status
        (case-insensitive ``FAILED`` / ``CANCELLED`` / ``CANCELED`` / ``ERROR``);
        success and any other unknown-but-non-PROCESSING status still return
        normally.
        """
        deadline = time.monotonic() + timeout_s
        while True:
            result = await self.retrieve(model=model, queue_id=queue_id)
            if result.status != _STATUS_PROCESSING:
                if (
                    raise_on_failed
                    and isinstance(result.status, str)
                    and result.status.upper() in _FAILURE_STATUSES
                ):
                    raise VeniceVideoFailedError(queue_id, result.status, result)
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
    ) -> VideoQueueResponse:
        body = _drop_none({"model": model, "prompt": prompt, "duration": duration, **extra})
        raw = self._client._request_json("POST", "/video/queue", json_body=body)
        return VideoQueueResponse.model_validate(raw)

    def retrieve(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> VideoRetrieveResponse:
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        raw = self._client._request_json("POST", "/video/retrieve", json_body=body)
        return VideoRetrieveResponse.model_validate(raw)

    def retrieve_binary(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> bytes:
        """Return the MP4 bytes straight from ``/video/retrieve``.

        Works for direct-bytes models; raises
        :class:`~veniceresch._errors.VeniceUnexpectedContentTypeError` for
        VPS-backed models (which return JSON). Prefer :meth:`download`.
        """
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

    def download(
        self,
        *,
        model: str,
        queue_id: str,
        download_url: str | None = None,
    ) -> bytes:
        """Return the MP4 bytes for a completed video, for any model family.

        Sync mirror of :meth:`AsyncVideoResource.download`.
        """
        if download_url is not None:
            return self._client._request_bytes("GET", download_url, no_auth=True)
        try:
            return self.retrieve_binary(model=model, queue_id=queue_id)
        except VeniceUnexpectedContentTypeError as exc:
            url = _download_url_from(exc)
            if url is None:
                raise
            return self._client._request_bytes("GET", url, no_auth=True)

    def quote(
        self,
        *,
        model: str,
        duration: str | None = None,
        **extra: Any,
    ) -> VideoQuoteResponse:
        body = _drop_none({"model": model, "duration": duration, **extra})
        raw = self._client._request_json("POST", "/video/quote", json_body=body)
        return VideoQuoteResponse.model_validate(raw)

    def complete(self, *, model: str, queue_id: str) -> VideoCompleteResponse:
        body = {"model": model, "queue_id": queue_id}
        raw = self._client._request_json("POST", "/video/complete", json_body=body)
        return VideoCompleteResponse.model_validate(raw)

    def transcribe(
        self, *, url: str, response_format: str | None = None
    ) -> VideoTranscriptionResponse:
        body = _drop_none({"url": url, "response_format": response_format})
        raw = self._client._request_json("POST", "/video/transcriptions", json_body=body)
        return VideoTranscriptionResponse.model_validate(raw)

    def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
        raise_on_failed: bool = False,
    ) -> VideoRetrieveResponse:
        """Sync mirror of :meth:`AsyncVideoResource.wait_for_completion`."""
        deadline = time.monotonic() + timeout_s
        while True:
            result = self.retrieve(model=model, queue_id=queue_id)
            if result.status != _STATUS_PROCESSING:
                if (
                    raise_on_failed
                    and isinstance(result.status, str)
                    and result.status.upper() in _FAILURE_STATUSES
                ):
                    raise VeniceVideoFailedError(queue_id, result.status, result)
                return result
            if time.monotonic() >= deadline:
                raise VeniceVideoTimeoutError(queue_id, timeout_s)
            time.sleep(poll_interval_s)


__all__ = [
    "AsyncVideoResource",
    "VeniceVideoFailedError",
    "VeniceVideoTimeoutError",
    "VideoResource",
]
