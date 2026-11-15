"""``/video/*`` resource.

Venice's video API is queue-based:

1. POST ``/video/queue`` with the generation parameters → receive a ``queue_id``.
2. Poll ``/video/retrieve`` with that ``queue_id`` until ``status == "COMPLETED"``.
3. Fetch the MP4 bytes with :meth:`download`.

``model`` is optional on the follow-up calls (``retrieve`` / ``complete`` /
``download`` / ``wait_for_completion``): Venice resolves the job from
``queue_id`` alone. ``prompt`` is optional on ``queue`` because enhancement /
upscale models (e.g. the Topaz family, driven by ``video_url`` plus
``enhancement_model`` / ``target_fps`` / ``slowdown_factor`` / …) take none.

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
from typing import TYPE_CHECKING, Any, NoReturn

from typing_extensions import deprecated

from veniceresch._content import _retrieve_body
from veniceresch._errors import VeniceAPIError, VeniceGoneError, VeniceUnexpectedContentTypeError
from veniceresch.resources._polling import (
    VeniceJobFailedError,
    is_failure_status,
    is_processing,
)
from veniceresch.types import (
    VideoCompleteResponse,
    VideoQueueResponse,
    VideoQuoteResponse,
    VideoRetrieveResponse,
)

if TYPE_CHECKING:
    import httpx

    from veniceresch._client import AsyncVeniceClient, VeniceClient


_DEFAULT_TIMEOUT_S = 600.0
_DEFAULT_POLL_S = 2.0
_TRANSCRIBE_DEPRECATION = (
    "video.transcribe() is gone (Venice retired /video/transcriptions); "
    "use chat.create with a video_url content part"
)
_TRANSCRIBE_GONE_MESSAGE = (
    "POST /video/transcriptions was retired by Venice and no longer serves data. "
    "For video analysis, use chat.create(...) with the video URL passed as a "
    "video_url content part, on a model whose "
    "model_spec.capabilities.supportsVideoInput is true (see models.list())."
)


def _transcribe_gone() -> NoReturn:
    raise VeniceGoneError(
        _TRANSCRIBE_GONE_MESSAGE,
        status_code=410,
        error_body={"error": _TRANSCRIBE_GONE_MESSAGE},
        link="/chat/completions",
    )


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


class VeniceVideoFailedError(VeniceJobFailedError):
    """Raised by :meth:`wait_for_completion` with ``raise_on_failed=True`` when
    the video job reaches a known failure terminal state.

    The final retrieve response is on :attr:`result` for inspection. The shared
    body lives on :class:`~veniceresch.resources._polling.VeniceJobFailedError`.
    """

    def __init__(self, queue_id: str, status: str, result: VideoRetrieveResponse) -> None:
        super().__init__(queue_id, status, result, kind="Video")


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _draft_fields(draft: bool | None, draft_task_id: str | None) -> dict[str, Any]:
    if draft and draft_task_id is not None:
        raise ValueError(
            "draft=True and draft_task_id can't be combined: draft_task_id upgrades an "
            "existing draft to HD (Venice rejects both)."
        )
    return {"draft": draft, "draft_task_id": draft_task_id}


def _video_retrieve_result(response: httpx.Response) -> VideoRetrieveResponse:
    payload = _retrieve_body(response, "/video/retrieve", "video")
    if isinstance(payload, bytes):
        return VideoRetrieveResponse(
            status="COMPLETED",
            video=payload,
            content_type=response.headers.get("content-type"),
        )
    return VideoRetrieveResponse.model_validate(payload)


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
        prompt: str | None = None,
        duration: str | None = None,
        draft: bool | None = None,
        draft_task_id: str | None = None,
        **extra: Any,
    ) -> VideoQueueResponse:
        """Queue a video job. Returns a :class:`VideoQueueResponse` with ``queue_id``.

        Fields not named here (``aspect_ratio``, ``resolution``, ``image_url``,
        ``image_references``, ``video_references``, …) go through ``**extra``.

        Draft mode (models with ``supportsDraftMode``, e.g. Seedance 2.5):
        ``draft=True`` renders a fast 480p draft; the response carries
        ``draft_task_id``. Queue again with ``draft_task_id=...`` (and no
        ``draft``) to upgrade it to HD before ``draft_expires_at``.
        """
        body = _drop_none(
            {
                "model": model,
                "prompt": prompt,
                "duration": duration,
                **_draft_fields(draft, draft_task_id),
                **extra,
            }
        )
        raw = await self._client._request_json("POST", "/video/queue", json_body=body)
        return VideoQueueResponse.model_validate(raw)

    async def retrieve(
        self,
        *,
        model: str | None = None,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
    ) -> VideoRetrieveResponse:
        """Poll the queue once. Returns a :class:`VideoRetrieveResponse`.

        ``status`` is ``"PROCESSING"`` while the job runs. Direct-bytes models
        answer with the finished MP4 once done: the result is then
        ``status="COMPLETED"`` with the bytes on ``.video``. VPS-backed models
        return a JSON ``COMPLETED`` status (``.video`` is ``None``); fetch their
        media with :meth:`download`.
        """
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        response = await self._client._send(
            "POST", "/video/retrieve", json_body=body, params=None, headers=None
        )
        return _video_retrieve_result(response)

    async def retrieve_binary(
        self,
        *,
        model: str | None = None,
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
        model: str | None = None,
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
        # A presigned/CDN URL is an opaque object-store download, not a Venice
        # API surface — object stores routinely serve real media as text/plain
        # when no Content-Type metadata is set, so guarding the content type here
        # would reject genuine bytes. Skip the guard for these fetches.
        if download_url is not None:
            return await self._client._request_bytes(
                "GET", download_url, no_auth=True, guard_content_type=False
            )
        try:
            return await self.retrieve_binary(model=model, queue_id=queue_id)
        except VeniceUnexpectedContentTypeError as exc:
            url = _download_url_from(exc)
            if url is None:
                raise
            return await self._client._request_bytes(
                "GET", url, no_auth=True, guard_content_type=False
            )

    async def quote(
        self,
        *,
        model: str,
        duration: str | None = None,
        draft: bool | None = None,
        draft_task_id: str | None = None,
        **extra: Any,
    ) -> VideoQuoteResponse:
        """Price a video job. ``draft`` / ``draft_task_id`` quote a draft or its
        HD upgrade (see :meth:`queue`); other fields go through ``**extra``."""
        body = _drop_none(
            {"model": model, "duration": duration, **_draft_fields(draft, draft_task_id), **extra}
        )
        raw = await self._client._request_json("POST", "/video/quote", json_body=body)
        return VideoQuoteResponse.model_validate(raw)

    async def complete(
        self,
        *,
        model: str | None = None,
        queue_id: str,
    ) -> VideoCompleteResponse:
        body = _drop_none({"model": model, "queue_id": queue_id})
        raw = await self._client._request_json("POST", "/video/complete", json_body=body)
        return VideoCompleteResponse.model_validate(raw)

    @deprecated(_TRANSCRIBE_DEPRECATION)
    async def transcribe(
        self,
        *,
        url: str,
        response_format: str | None = None,
    ) -> NoReturn:
        """Deprecated: Venice retired ``/video/transcriptions`` (HTTP 410).

        Always raises :class:`~veniceresch._errors.VeniceGoneError` (no
        network call). For video analysis, summaries or questions about a
        video, call ``chat.create`` with the video URL as a ``video_url``
        content part on a model whose
        ``model_spec.capabilities.supportsVideoInput`` is true. Removed in 1.0.
        """
        _transcribe_gone()

    async def wait_for_completion(
        self,
        *,
        model: str | None = None,
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

        For models that answer the final poll with the finished file, the
        returned result already carries it on ``.video``; otherwise
        (``.video`` is ``None``) fetch the media with :meth:`download`.
        """
        deadline = time.monotonic() + timeout_s
        while True:
            result = await self.retrieve(model=model, queue_id=queue_id)
            if not is_processing(result.status):
                if raise_on_failed and is_failure_status(result.status):
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
        prompt: str | None = None,
        duration: str | None = None,
        draft: bool | None = None,
        draft_task_id: str | None = None,
        **extra: Any,
    ) -> VideoQueueResponse:
        """Sync mirror of :meth:`AsyncVideoResource.queue`."""
        body = _drop_none(
            {
                "model": model,
                "prompt": prompt,
                "duration": duration,
                **_draft_fields(draft, draft_task_id),
                **extra,
            }
        )
        raw = self._client._request_json("POST", "/video/queue", json_body=body)
        return VideoQueueResponse.model_validate(raw)

    def retrieve(
        self,
        *,
        model: str | None = None,
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
        response = self._client._send(
            "POST", "/video/retrieve", json_body=body, params=None, headers=None
        )
        return _video_retrieve_result(response)

    def retrieve_binary(
        self,
        *,
        model: str | None = None,
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
        model: str | None = None,
        queue_id: str,
        download_url: str | None = None,
    ) -> bytes:
        """Return the MP4 bytes for a completed video, for any model family.

        Sync mirror of :meth:`AsyncVideoResource.download`.
        """
        # See AsyncVideoResource.download: presigned URLs are opaque downloads,
        # so the binary content-type guard is skipped for them.
        if download_url is not None:
            return self._client._request_bytes(
                "GET", download_url, no_auth=True, guard_content_type=False
            )
        try:
            return self.retrieve_binary(model=model, queue_id=queue_id)
        except VeniceUnexpectedContentTypeError as exc:
            url = _download_url_from(exc)
            if url is None:
                raise
            return self._client._request_bytes("GET", url, no_auth=True, guard_content_type=False)

    def quote(
        self,
        *,
        model: str,
        duration: str | None = None,
        draft: bool | None = None,
        draft_task_id: str | None = None,
        **extra: Any,
    ) -> VideoQuoteResponse:
        """Sync mirror of :meth:`AsyncVideoResource.quote`."""
        body = _drop_none(
            {"model": model, "duration": duration, **_draft_fields(draft, draft_task_id), **extra}
        )
        raw = self._client._request_json("POST", "/video/quote", json_body=body)
        return VideoQuoteResponse.model_validate(raw)

    def complete(self, *, model: str | None = None, queue_id: str) -> VideoCompleteResponse:
        body = _drop_none({"model": model, "queue_id": queue_id})
        raw = self._client._request_json("POST", "/video/complete", json_body=body)
        return VideoCompleteResponse.model_validate(raw)

    @deprecated(_TRANSCRIBE_DEPRECATION)
    def transcribe(self, *, url: str, response_format: str | None = None) -> NoReturn:
        """Sync mirror of :meth:`AsyncVideoResource.transcribe` (deprecated)."""
        _transcribe_gone()

    def wait_for_completion(
        self,
        *,
        model: str | None = None,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
        raise_on_failed: bool = False,
    ) -> VideoRetrieveResponse:
        """Sync mirror of :meth:`AsyncVideoResource.wait_for_completion`."""
        deadline = time.monotonic() + timeout_s
        while True:
            result = self.retrieve(model=model, queue_id=queue_id)
            if not is_processing(result.status):
                if raise_on_failed and is_failure_status(result.status):
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
