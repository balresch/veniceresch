"""``/audio/*`` resource: TTS, transcription, and queued audio generation.

Mirrors the video API's shape: ``speech`` is synchronous, everything else goes
through the queue/retrieve/complete flow that also exists for video. A
:meth:`wait_for_completion` helper polls ``/audio/retrieve`` until done.

``client.audio.voice_changer`` wraps the separate speech-to-speech family under
``/audio/voice-changer/*`` (queue / quote / retrieve / complete). Its retrieve
answers with JSON while the job runs and with the audio *bytes* once it is
done; :class:`~veniceresch.types.VoiceChangerRetrieveResponse` folds both into
one result.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from veniceresch._errors import VeniceAPIError
from veniceresch.resources._polling import (
    VeniceJobFailedError,
    is_failure_status,
    is_processing,
)
from veniceresch.resources._uploads import UploadInput, async_open_upload, open_upload
from veniceresch.types import (
    AudioCompleteResponse,
    AudioQueueResponse,
    AudioQuoteResponse,
    AudioRetrieveResponse,
    AudioTranscriptionResponse,
    ClonedVoiceResponse,
    VoiceChangerQueueResponse,
    VoiceChangerQuoteResponse,
    VoiceChangerRetrieveResponse,
)

if TYPE_CHECKING:
    import httpx

    from veniceresch._client import AsyncVeniceClient, VeniceClient


# bytes | str | Path | binary file-like object. See ``_uploads.open_upload``.
AudioInput = UploadInput
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


class VeniceAudioFailedError(VeniceJobFailedError):
    """Raised by :meth:`wait_for_completion` with ``raise_on_failed=True`` when
    the audio job reaches a known failure terminal state.

    The final retrieve response is on :attr:`result` for inspection. The shared
    body lives on :class:`~veniceresch.resources._polling.VeniceJobFailedError`.
    """

    def __init__(self, queue_id: str, status: str, result: AudioRetrieveResponse) -> None:
        super().__init__(queue_id, status, result, kind="Audio")


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


# ---- voice changer helpers ------------------------------------------------

_VC = "/audio/voice-changer"


def _form_value(value: Any) -> str:
    # Multipart fields are strings on the wire. Render booleans the way JSON
    # does ("true"/"false") rather than Python's "True"/"False".
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _vc_queue_fields(
    *,
    model: str,
    file: AudioInput | None,
    audio_url: str | None,
    voice: str | None,
    remove_background_noise: bool | None,
    seed: int | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    if (file is None) == (audio_url is None):
        raise ValueError("Supply exactly one of file= or audio_url= (Venice rejects both/neither).")
    return _drop_none(
        {
            "model": model,
            "audio_url": audio_url,
            "voice": voice,
            "remove_background_noise": remove_background_noise,
            "seed": seed,
            **extra,
        }
    )


def _header_float(response: httpx.Response, name: str) -> float | None:
    value = response.headers.get(name)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _vc_retrieve_result(response: httpx.Response) -> VoiceChangerRetrieveResponse:
    content_type = response.headers.get("content-type", "")
    if content_type.split(";", 1)[0].strip().lower() == "application/json":
        return VoiceChangerRetrieveResponse.model_validate(response.json())
    return VoiceChangerRetrieveResponse(
        status="COMPLETED",
        audio=response.content,
        content_type=content_type or None,
        audio_format=response.headers.get("x-venice-audio-format"),
        audio_duration=_header_float(response, "x-venice-audio-duration"),
        inference_time=_header_float(response, "x-venice-inference-time"),
        model_id=response.headers.get("x-venice-model-id"),
        model_name=response.headers.get("x-venice-model-name"),
    )


def _vc_accept(accept: str) -> dict[str, str]:
    # Ask for the audio bytes but also accept the JSON "still processing" body.
    return {"Accept": f"{accept}, application/json"}


class AsyncVoiceChangerResource:
    """Speech-to-speech conversion. Accessed via ``client.audio.voice_changer``.

    Flow: :meth:`quote` (optional) → :meth:`queue` → :meth:`wait_for_completion`
    (or poll :meth:`retrieve`) → :meth:`complete` to release provider-held
    media (unnecessary if you pass ``delete_media_on_completion=True``).

    A queued conversion is charged immediately, so :meth:`queue` is **not**
    safe to retry: if its response is lost, poll :meth:`retrieve` instead of
    queueing again.
    """

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def queue(
        self,
        *,
        model: str,
        file: AudioInput | None = None,
        audio_url: str | None = None,
        voice: str | None = None,
        remove_background_noise: bool | None = None,
        seed: int | None = None,
        **extra: Any,
    ) -> VoiceChangerQueueResponse:
        """Queue a voice conversion of a source recording.

        Pass exactly one of ``file`` (raw ``bytes``, a path, or a binary
        file-like object — sent as a multipart upload) or ``audio_url`` (an
        http(s) URL Venice fetches itself — sent as JSON). ``voice`` is one of
        the model's ``voices`` (or a provider voice ID when the model reports
        ``supports_custom_voice_id``); it defaults to the model's
        ``default_voice``.
        """
        fields = _vc_queue_fields(
            model=model,
            file=file,
            audio_url=audio_url,
            voice=voice,
            remove_background_noise=remove_background_noise,
            seed=seed,
            extra=extra,
        )
        if file is None:
            raw = await self._client._request_json("POST", f"{_VC}/queue", json_body=fields)
        else:
            form = {k: _form_value(v) for k, v in fields.items()}
            async with async_open_upload(file, default_name="audio.bin") as file_tuple:
                raw = await self._client._request_json(
                    "POST", f"{_VC}/queue", files={"file": file_tuple}, data=form
                )
        return VoiceChangerQueueResponse.model_validate(raw)

    async def quote(self, *, model: str, duration_seconds: float) -> VoiceChangerQuoteResponse:
        """Estimate the price (USD) of converting a recording of this length.

        Billing rounds the source length up to the next whole minute, measured
        server-side at queue time, so this is an estimate.
        """
        body = {"model": model, "duration_seconds": duration_seconds}
        raw = await self._client._request_json("POST", f"{_VC}/quote", json_body=body)
        return VoiceChangerQuoteResponse.model_validate(raw)

    async def retrieve(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
        accept: str = "audio/mpeg",
    ) -> VoiceChangerRetrieveResponse:
        """Poll a conversion once.

        Returns ``status="PROCESSING"`` while it runs, or ``status="COMPLETED"``
        with the converted bytes on ``.audio`` once done (see
        :class:`~veniceresch.types.VoiceChangerRetrieveResponse`). A failed
        conversion is reported as an HTTP error and raises the matching
        :class:`~veniceresch._errors.VeniceAPIError` subclass; its
        ``error_body`` carries ``credits_refunded``.
        """
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        response = await self._client._send(
            "POST", f"{_VC}/retrieve", json_body=body, params=None, headers=_vc_accept(accept)
        )
        return _vc_retrieve_result(response)

    async def complete(self, *, model: str, queue_id: str) -> AudioCompleteResponse:
        """Release provider-held media for a finished conversion (idempotent)."""
        body = {"model": model, "queue_id": queue_id}
        raw = await self._client._request_json("POST", f"{_VC}/complete", json_body=body)
        return AudioCompleteResponse.model_validate(raw)

    async def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
        delete_media_on_completion: bool | None = None,
        raise_on_failed: bool = False,
        accept: str = "audio/mpeg",
    ) -> VoiceChangerRetrieveResponse:
        """Poll :meth:`retrieve` until the conversion leaves ``PROCESSING``.

        On success the returned result carries the audio bytes on ``.audio``.
        Raises :class:`VeniceAudioTimeoutError` if ``timeout_s`` elapses first.
        ``raise_on_failed`` behaves as on :meth:`AsyncAudioResource.wait_for_completion`.
        """
        deadline = time.monotonic() + timeout_s
        while True:
            result = await self.retrieve(
                model=model,
                queue_id=queue_id,
                delete_media_on_completion=delete_media_on_completion,
                accept=accept,
            )
            if not is_processing(result.status):
                if raise_on_failed and is_failure_status(result.status):
                    raise VeniceAudioFailedError(queue_id, result.status, result)
                return result
            if time.monotonic() >= deadline:
                raise VeniceAudioTimeoutError(queue_id, timeout_s)
            await asyncio.sleep(poll_interval_s)


class VoiceChangerResource:
    """Sync mirror of :class:`AsyncVoiceChangerResource`."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def queue(
        self,
        *,
        model: str,
        file: AudioInput | None = None,
        audio_url: str | None = None,
        voice: str | None = None,
        remove_background_noise: bool | None = None,
        seed: int | None = None,
        **extra: Any,
    ) -> VoiceChangerQueueResponse:
        """Sync mirror of :meth:`AsyncVoiceChangerResource.queue`."""
        fields = _vc_queue_fields(
            model=model,
            file=file,
            audio_url=audio_url,
            voice=voice,
            remove_background_noise=remove_background_noise,
            seed=seed,
            extra=extra,
        )
        if file is None:
            raw = self._client._request_json("POST", f"{_VC}/queue", json_body=fields)
        else:
            form = {k: _form_value(v) for k, v in fields.items()}
            with open_upload(file, default_name="audio.bin") as file_tuple:
                raw = self._client._request_json(
                    "POST", f"{_VC}/queue", files={"file": file_tuple}, data=form
                )
        return VoiceChangerQueueResponse.model_validate(raw)

    def quote(self, *, model: str, duration_seconds: float) -> VoiceChangerQuoteResponse:
        """Sync mirror of :meth:`AsyncVoiceChangerResource.quote`."""
        body = {"model": model, "duration_seconds": duration_seconds}
        raw = self._client._request_json("POST", f"{_VC}/quote", json_body=body)
        return VoiceChangerQuoteResponse.model_validate(raw)

    def retrieve(
        self,
        *,
        model: str,
        queue_id: str,
        delete_media_on_completion: bool | None = None,
        accept: str = "audio/mpeg",
    ) -> VoiceChangerRetrieveResponse:
        """Sync mirror of :meth:`AsyncVoiceChangerResource.retrieve`."""
        body = _drop_none(
            {
                "model": model,
                "queue_id": queue_id,
                "delete_media_on_completion": delete_media_on_completion,
            }
        )
        response = self._client._send(
            "POST", f"{_VC}/retrieve", json_body=body, params=None, headers=_vc_accept(accept)
        )
        return _vc_retrieve_result(response)

    def complete(self, *, model: str, queue_id: str) -> AudioCompleteResponse:
        """Sync mirror of :meth:`AsyncVoiceChangerResource.complete`."""
        body = {"model": model, "queue_id": queue_id}
        raw = self._client._request_json("POST", f"{_VC}/complete", json_body=body)
        return AudioCompleteResponse.model_validate(raw)

    def wait_for_completion(
        self,
        *,
        model: str,
        queue_id: str,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_interval_s: float = _DEFAULT_POLL_S,
        delete_media_on_completion: bool | None = None,
        raise_on_failed: bool = False,
        accept: str = "audio/mpeg",
    ) -> VoiceChangerRetrieveResponse:
        """Sync mirror of :meth:`AsyncVoiceChangerResource.wait_for_completion`."""
        deadline = time.monotonic() + timeout_s
        while True:
            result = self.retrieve(
                model=model,
                queue_id=queue_id,
                delete_media_on_completion=delete_media_on_completion,
                accept=accept,
            )
            if not is_processing(result.status):
                if raise_on_failed and is_failure_status(result.status):
                    raise VeniceAudioFailedError(queue_id, result.status, result)
                return result
            if time.monotonic() >= deadline:
                raise VeniceAudioTimeoutError(queue_id, timeout_s)
            time.sleep(poll_interval_s)


class AsyncAudioResource:
    """Async audio resource. Accessed via ``client.audio``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client
        self.voice_changer = AsyncVoiceChangerResource(client)

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

        ``file`` may be raw ``bytes``, a path (``str`` / :class:`~pathlib.Path`,
        streamed), or a binary file-like object (streamed; you keep ownership).
        """
        form = _drop_none(
            {
                "model": model,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        headers = {"SIGN-IN-WITH-X": siwx_header} if siwx_header is not None else None
        async with async_open_upload(file, default_name="audio.bin") as file_tuple:
            raw = await self._client._request_json(
                "POST",
                "/audio/voices",
                files={"file": file_tuple},
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
        """Transcribe an audio file (multipart upload).

        ``file`` may be raw ``bytes``, a path (``str`` / :class:`~pathlib.Path`,
        streamed), or a binary file-like object (streamed; you keep ownership).
        """
        form = _drop_none(
            {
                "model": model,
                "response_format": response_format,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        async with async_open_upload(file, default_name="audio.bin") as file_tuple:
            raw = await self._client._request_json(
                "POST",
                "/audio/transcriptions",
                files={"file": file_tuple},
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
            if not is_processing(result.status):
                if raise_on_failed and is_failure_status(result.status):
                    raise VeniceAudioFailedError(queue_id, result.status, result)
                return result
            if time.monotonic() >= deadline:
                raise VeniceAudioTimeoutError(queue_id, timeout_s)
            await asyncio.sleep(poll_interval_s)


class AudioResource:
    """Sync audio resource."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client
        self.voice_changer = VoiceChangerResource(client)

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
        form = _drop_none(
            {
                "model": model,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        headers = {"SIGN-IN-WITH-X": siwx_header} if siwx_header is not None else None
        with open_upload(file, default_name="audio.bin") as file_tuple:
            raw = self._client._request_json(
                "POST",
                "/audio/voices",
                files={"file": file_tuple},
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
        """Sync mirror of :meth:`AsyncAudioResource.transcribe`."""
        form = _drop_none(
            {
                "model": model,
                "response_format": response_format,
                **{k: str(v) for k, v in extra.items() if v is not None},
            }
        )
        with open_upload(file, default_name="audio.bin") as file_tuple:
            raw = self._client._request_json(
                "POST",
                "/audio/transcriptions",
                files={"file": file_tuple},
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
            if not is_processing(result.status):
                if raise_on_failed and is_failure_status(result.status):
                    raise VeniceAudioFailedError(queue_id, result.status, result)
                return result
            if time.monotonic() >= deadline:
                raise VeniceAudioTimeoutError(queue_id, timeout_s)
            time.sleep(poll_interval_s)


__all__ = [
    "AsyncAudioResource",
    "AsyncVoiceChangerResource",
    "AudioResource",
    "VeniceAudioFailedError",
    "VeniceAudioTimeoutError",
    "VoiceChangerResource",
]
