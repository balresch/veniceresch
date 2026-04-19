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

from venice_sdk._errors import VeniceAPIError

if TYPE_CHECKING:
    from venice_sdk._client import AsyncVeniceClient, VeniceClient


AudioInput = bytes | str | Path
_STATUS_PROCESSING = "PROCESSING"
_DEFAULT_TIMEOUT_S = 300.0
_DEFAULT_POLL_S = 2.0


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

    async def transcribe(
        self,
        *,
        file: AudioInput,
        model: str | None = None,
        response_format: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Transcribe an audio file (multipart upload)."""
        files = {"file": _audio_file_tuple(file)}
        form = _drop_none(
            {
                "model": model,
                "response_format": response_format,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        return await self._client._request_json(
            "POST",
            "/audio/transcriptions",
            files=files,
            data=form,
        )

    async def queue(
        self,
        *,
        model: str,
        prompt: str,
        **extra: Any,
    ) -> dict[str, Any]:
        body = _drop_none({"model": model, "prompt": prompt, **extra})
        return await self._client._request_json("POST", "/audio/queue", json_body=body)

    async def retrieve(self, *, model: str, queue_id: str, **extra: Any) -> dict[str, Any]:
        body = _drop_none({"model": model, "queue_id": queue_id, **extra})
        return await self._client._request_json("POST", "/audio/retrieve", json_body=body)

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

    async def quote(self, *, model: str, **extra: Any) -> dict[str, Any]:
        body = _drop_none({"model": model, **extra})
        return await self._client._request_json("POST", "/audio/quote", json_body=body)

    async def complete(self, *, model: str, queue_id: str) -> dict[str, Any]:
        body = {"model": model, "queue_id": queue_id}
        return await self._client._request_json("POST", "/audio/complete", json_body=body)

    async def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        while True:
            result = await self.retrieve(model=model, queue_id=queue_id)
            if result.get("status") != _STATUS_PROCESSING:
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

    def transcribe(
        self,
        *,
        file: AudioInput,
        model: str | None = None,
        response_format: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        files = {"file": _audio_file_tuple(file)}
        form = _drop_none(
            {
                "model": model,
                "response_format": response_format,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        return self._client._request_json(
            "POST",
            "/audio/transcriptions",
            files=files,
            data=form,
        )

    def queue(self, *, model: str, prompt: str, **extra: Any) -> dict[str, Any]:
        body = _drop_none({"model": model, "prompt": prompt, **extra})
        return self._client._request_json("POST", "/audio/queue", json_body=body)

    def retrieve(self, *, model: str, queue_id: str, **extra: Any) -> dict[str, Any]:
        body = _drop_none({"model": model, "queue_id": queue_id, **extra})
        return self._client._request_json("POST", "/audio/retrieve", json_body=body)

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

    def quote(self, *, model: str, **extra: Any) -> dict[str, Any]:
        body = _drop_none({"model": model, **extra})
        return self._client._request_json("POST", "/audio/quote", json_body=body)

    def complete(self, *, model: str, queue_id: str) -> dict[str, Any]:
        body = {"model": model, "queue_id": queue_id}
        return self._client._request_json("POST", "/audio/complete", json_body=body)

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
                raise VeniceAudioTimeoutError(queue_id, timeout_s)
            time.sleep(poll_interval_s)


__all__ = [
    "AsyncAudioResource",
    "AudioResource",
    "VeniceAudioTimeoutError",
]
