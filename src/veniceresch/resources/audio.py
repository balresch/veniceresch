"""``/audio/*`` resource: TTS, transcription, and queued audio generation.

Mirrors the video API's shape: ``speech`` is synchronous, everything else goes
through the queue/retrieve/complete flow that also exists for video. A
:meth:`wait_for_completion` helper polls ``/audio/retrieve`` until done.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from veniceresch._errors import VeniceAPIError
from veniceresch.types import (
    AudioCompleteResponse,
    AudioQueueResponse,
    AudioQuoteResponse,
    AudioRetrieveResponse,
    AudioTranscriptionResponse,
    ClonedVoiceResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


AudioInput = bytes | str | Path
_STATUS_PROCESSING = "PROCESSING"
_DEFAULT_TIMEOUT_S = 300.0
_DEFAULT_POLL_S = 2.0
# Venice does not document failure status strings for /audio/retrieve (the
# swagger enum lists PROCESSING only). This curated, case-insensitive set is
# what ``wait_for_completion(raise_on_failed=True)`` treats as failure; any
# other non-PROCESSING status (including unknown ones) still returns normally,
# preserving the "tolerate unknown terminal statuses" contract.
_FAILURE_STATUSES = frozenset({"FAILED", "CANCELLED", "CANCELED", "ERROR"})


class VeniceAudioTimeoutError(VeniceAPIError):
    """Raised when :meth:`wait_for_completion` exceeds its timeout."""

    def __init__(self, queue_id: str, timeout_s: float) -> None:
        super().__init__(
            f"Audio queue_id={queue_id!r} did not complete within {timeout_s:.1f}s",
            status_code=0,
            error_body={"queue_id": queue_id, "timeout_s": timeout_s},
        )
        self.queue_id = queue_id
        self.timeout_s = timeout_s


class VeniceAudioFailedError(VeniceAPIError):
    """Raised by :meth:`wait_for_completion` with ``raise_on_failed=True`` when
    the job reaches a known failure terminal state (see ``_FAILURE_STATUSES``).

    The final retrieve response is on :attr:`result` for inspection.
    """

    def __init__(self, queue_id: str, status: str, result: AudioRetrieveResponse) -> None:
        super().__init__(
            f"Audio queue_id={queue_id!r} ended in failure status {status!r}",
            status_code=0,
            error_body={"queue_id": queue_id, "status": status},
        )
        self.queue_id = queue_id
        self.status = status
        self.result = result


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _audio_file_tuple(audio: AudioInput) -> tuple[str, bytes, str]:
    """Build a (filename, bytes, content-type) tuple for multipart upload."""
    if isinstance(audio, bytes):
        return ("audio.bin", audio, "application/octet-stream")
    if isinstance(audio, Path):
        return (audio.name, audio.read_bytes(), "application/octet-stream")
    # str — treat as path
    p = Path(audio)
    return (p.name, p.read_bytes(), "application/octet-stream")


class AsyncAudioResource:
    """Async audio resource. Accessed via ``client.audio``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def create_speech(
        self,
        *,
        input: str,
        voice: str | None = None,
        model: str | None = None,
        response_format: str | None = None,
        **extra: Any,
    ) -> bytes:
        """Text-to-speech. Returns raw audio bytes in the requested format."""
        body = _drop_none(
            {
                "input": input,
                "voice": voice,
                "model": model,
                "response_format": response_format,
                **extra,
            }
        )
        return await self._client._request_bytes("POST", "/audio/speech", json_body=body)

    async def create_cloned_voice(
        self,
        *,
        file: AudioInput,
        model: str | None = None,
        siwx_header: str | None = None,
        **extra: Any,
    ) -> ClonedVoiceResponse:
        """Clone a voice from an audio sample (multipart upload).

        Returns a ``vv_<id>`` voice handle (on ``.id``) to pass back as the
        ``voice`` argument to :meth:`create_speech` alongside the same
        ``model``. Pass ``siwx_header`` to authenticate with an x402 wallet
        instead of the default Bearer key.
        """
        files = {"file": _audio_file_tuple(file)}
        form = _drop_none(
            {
                "model": model,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        headers = {"SIGN-IN-WITH-X": siwx_header} if siwx_header is not None else None
        raw = await self._client._request_json(
            "POST",
            "/audio/voices",
            files=files,
            data=form,
            headers=headers,
            no_auth=siwx_header is not None,
        )
        return ClonedVoiceResponse.model_validate(raw)

    async def transcribe(
        self,
        *,
        file: AudioInput,
        model: str | None = None,
        response_format: str | None = None,
        **extra: Any,
    ) -> AudioTranscriptionResponse:
        """Transcribe an audio file (multipart upload)."""
        files = {"file": _audio_file_tuple(file)}
        form = _drop_none(
            {
                "model": model,
                "response_format": response_format,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        raw = await self._client._request_json(
            "POST",
            "/audio/transcriptions",
            files=files,
            data=form,
        )
        return AudioTranscriptionResponse.model_validate(raw)

    async def queue(
        self,
        *,
        model: str,
        prompt: str,
        **extra: Any,
    ) -> AudioQueueResponse:
        body = _drop_none({"model": model, "prompt": prompt, **extra})
        raw = await self._client._request_json("POST", "/audio/queue", json_body=body)
        return AudioQueueResponse.model_validate(raw)

    async def retrieve(self, *, model: str, queue_id: str, **extra: Any) -> AudioRetrieveResponse:
        body = _drop_none({"model": model, "queue_id": queue_id, **extra})
        raw = await self._client._request_json("POST", "/audio/retrieve", json_body=body)
        return AudioRetrieveResponse.model_validate(raw)

    async def retrieve_binary(
        self,
        *,
        model: str,
        queue_id: str,
        accept: str = "audio/mpeg",
        **extra: Any,
    ) -> bytes:
        body = _drop_none({"model": model, "queue_id": queue_id, **extra})
        return await self._client._request_bytes(
            "POST",
            "/audio/retrieve",
            json_body=body,
            headers={"Accept": accept},
        )

    async def quote(self, *, model: str, **extra: Any) -> AudioQuoteResponse:
        body = _drop_none({"model": model, **extra})
        raw = await self._client._request_json("POST", "/audio/quote", json_body=body)
        return AudioQuoteResponse.model_validate(raw)

    async def complete(self, *, model: str, queue_id: str) -> AudioCompleteResponse:
        body = {"model": model, "queue_id": queue_id}
        raw = await self._client._request_json("POST", "/audio/complete", json_body=body)
        return AudioCompleteResponse.model_validate(raw)

    async def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
        raise_on_failed: bool = False,
    ) -> AudioRetrieveResponse:
        """Poll ``/audio/retrieve`` until the job reaches a *terminal* state.

        Waits for a terminal state, not necessarily a *successful* one: by
        default it returns the final retrieve response for any non-PROCESSING
        status, preserving tolerance of undocumented terminal statuses. Raises
        :class:`VeniceAudioTimeoutError` if ``timeout_s`` elapses first.

        Pass ``raise_on_failed=True`` to instead raise
        :class:`VeniceAudioFailedError` on a known failure status
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
                    raise VeniceAudioFailedError(queue_id, result.status, result)
                return result
            if time.monotonic() >= deadline:
                raise VeniceAudioTimeoutError(queue_id, timeout_s)
            await asyncio.sleep(poll_interval_s)


class AudioResource:
    """Sync audio resource."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def create_speech(
        self,
        *,
        input: str,
        voice: str | None = None,
        model: str | None = None,
        response_format: str | None = None,
        **extra: Any,
    ) -> bytes:
        body = _drop_none(
            {
                "input": input,
                "voice": voice,
                "model": model,
                "response_format": response_format,
                **extra,
            }
        )
        return self._client._request_bytes("POST", "/audio/speech", json_body=body)

    def create_cloned_voice(
        self,
        *,
        file: AudioInput,
        model: str | None = None,
        siwx_header: str | None = None,
        **extra: Any,
    ) -> ClonedVoiceResponse:
        """Sync mirror of :meth:`AsyncAudioResource.create_cloned_voice`."""
        files = {"file": _audio_file_tuple(file)}
        form = _drop_none(
            {
                "model": model,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        headers = {"SIGN-IN-WITH-X": siwx_header} if siwx_header is not None else None
        raw = self._client._request_json(
            "POST",
            "/audio/voices",
            files=files,
            data=form,
            headers=headers,
            no_auth=siwx_header is not None,
        )
        return ClonedVoiceResponse.model_validate(raw)

    def transcribe(
        self,
        *,
        file: AudioInput,
        model: str | None = None,
        response_format: str | None = None,
        **extra: Any,
    ) -> AudioTranscriptionResponse:
        files = {"file": _audio_file_tuple(file)}
        form = _drop_none(
            {
                "model": model,
                "response_format": response_format,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        raw = self._client._request_json(
            "POST",
            "/audio/transcriptions",
            files=files,
            data=form,
        )
        return AudioTranscriptionResponse.model_validate(raw)

    def queue(self, *, model: str, prompt: str, **extra: Any) -> AudioQueueResponse:
        body = _drop_none({"model": model, "prompt": prompt, **extra})
        raw = self._client._request_json("POST", "/audio/queue", json_body=body)
        return AudioQueueResponse.model_validate(raw)

    def retrieve(self, *, model: str, queue_id: str, **extra: Any) -> AudioRetrieveResponse:
        body = _drop_none({"model": model, "queue_id": queue_id, **extra})
        raw = self._client._request_json("POST", "/audio/retrieve", json_body=body)
        return AudioRetrieveResponse.model_validate(raw)

    def retrieve_binary(
        self,
        *,
        model: str,
        queue_id: str,
        accept: str = "audio/mpeg",
        **extra: Any,
    ) -> bytes:
        body = _drop_none({"model": model, "queue_id": queue_id, **extra})
        return self._client._request_bytes(
            "POST",
            "/audio/retrieve",
            json_body=body,
            headers={"Accept": accept},
        )

    def quote(self, *, model: str, **extra: Any) -> AudioQuoteResponse:
        body = _drop_none({"model": model, **extra})
        raw = self._client._request_json("POST", "/audio/quote", json_body=body)
        return AudioQuoteResponse.model_validate(raw)

    def complete(self, *, model: str, queue_id: str) -> AudioCompleteResponse:
        body = {"model": model, "queue_id": queue_id}
        raw = self._client._request_json("POST", "/audio/complete", json_body=body)
        return AudioCompleteResponse.model_validate(raw)

    def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
        raise_on_failed: bool = False,
    ) -> AudioRetrieveResponse:
        """Sync mirror of :meth:`AsyncAudioResource.wait_for_completion`."""
        deadline = time.monotonic() + timeout_s
        while True:
            result = self.retrieve(model=model, queue_id=queue_id)
            if result.status != _STATUS_PROCESSING:
                if (
                    raise_on_failed
                    and isinstance(result.status, str)
                    and result.status.upper() in _FAILURE_STATUSES
                ):
                    raise VeniceAudioFailedError(queue_id, result.status, result)
                return result
            if time.monotonic() >= deadline:
                raise VeniceAudioTimeoutError(queue_id, timeout_s)
            time.sleep(poll_interval_s)


__all__ = [
    "AsyncAudioResource",
    "AudioResource",
    "VeniceAudioFailedError",
    "VeniceAudioTimeoutError",
]
