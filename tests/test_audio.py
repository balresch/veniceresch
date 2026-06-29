"""Tests for the audio resource."""

from __future__ import annotations

import io
import json

import httpx
import pytest

from veniceresch import VeniceAudioFailedError, VeniceAudioTimeoutError


async def test_create_speech_returns_bytes(mock_api, async_client):
    route = mock_api.post("/audio/speech").respond(200, content=b"MP3DATA")
    result = await async_client.audio.create_speech(
        input="hello there",
        voice="nova",
        model="tts-1",
        response_format="mp3",
    )
    assert result == b"MP3DATA"
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "input": "hello there",
        "voice": "nova",
        "model": "tts-1",
        "response_format": "mp3",
    }


async def test_transcribe_multipart_upload(mock_api, async_client, tmp_path):
    audio_path = tmp_path / "clip.wav"
    audio_path.write_bytes(b"WAVDATA")
    route = mock_api.post("/audio/transcriptions").respond(
        200,
        json={"text": "transcript"},
    )
    result = await async_client.audio.transcribe(
        file=audio_path,
        model="whisper-1",
        response_format="json",
    )
    assert result.text == "transcript"
    # Request should be multipart form, not JSON.
    content_type = route.calls.last.request.headers["content-type"]
    assert content_type.startswith("multipart/form-data")
    body = route.calls.last.request.content
    assert b"WAVDATA" in body
    assert b"whisper-1" in body


async def test_transcribe_accepts_string_path(mock_api, async_client, tmp_path):
    audio_path = tmp_path / "clip.wav"
    audio_path.write_bytes(b"WAVDATA")
    route = mock_api.post("/audio/transcriptions").respond(200, json={"text": "ok"})
    await async_client.audio.transcribe(file=str(audio_path), model="whisper-1")
    raw = route.calls.last.request.content
    assert b'filename="clip.wav"' in raw
    assert b"WAVDATA" in raw


async def test_transcribe_accepts_raw_bytes(mock_api, async_client):
    route = mock_api.post("/audio/transcriptions").respond(200, json={"text": "ok"})
    await async_client.audio.transcribe(file=b"RAWAUDIO", model="whisper-1")
    raw = route.calls.last.request.content
    assert b'filename="audio.bin"' in raw  # default name for bytes
    assert b"RAWAUDIO" in raw


async def test_transcribe_accepts_file_like(mock_api, async_client):
    route = mock_api.post("/audio/transcriptions").respond(200, json={"text": "ok"})
    handle = io.BytesIO(b"STREAMED")
    await async_client.audio.transcribe(file=handle, model="whisper-1")
    raw = route.calls.last.request.content
    assert b"STREAMED" in raw
    # We never close a caller-supplied handle.
    assert not handle.closed


async def test_transcribe_missing_path_raises(async_client, tmp_path):
    with pytest.raises(FileNotFoundError):
        await async_client.audio.transcribe(file=tmp_path / "nope.wav", model="whisper-1")


async def test_create_cloned_voice_multipart(mock_api, async_client, tmp_path):
    sample = tmp_path / "voice.mp3"
    sample.write_bytes(b"MP3SAMPLE")
    route = mock_api.post("/audio/voices").respond(
        200,
        json={"id": "vv_abc123", "model": "tts-chatterbox-hd"},
    )
    result = await async_client.audio.create_cloned_voice(
        file=sample,
        model="tts-chatterbox-hd",
    )
    assert result.id == "vv_abc123"
    assert result.model == "tts-chatterbox-hd"
    req = route.calls.last.request
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b"MP3SAMPLE" in req.content
    assert b"tts-chatterbox-hd" in req.content
    # Default bearer auth is used when no siwx header is given.
    assert req.headers["Authorization"].startswith("Bearer ")


async def test_create_cloned_voice_siwx(mock_api, async_client, tmp_path):
    sample = tmp_path / "voice.wav"
    sample.write_bytes(b"WAVSAMPLE")
    route = mock_api.post("/audio/voices").respond(
        200, json={"id": "vv_xyz", "model": "tts-minimax-speech-02-hd"}
    )
    await async_client.audio.create_cloned_voice(
        file=sample,
        model="tts-minimax-speech-02-hd",
        siwx_header="siwx-payload",
    )
    req = route.calls.last.request
    assert req.headers["SIGN-IN-WITH-X"] == "siwx-payload"
    assert "Authorization" not in req.headers


async def test_audio_queue(mock_api, async_client):
    route = mock_api.post("/audio/queue").respond(
        200, json={"model": "a", "queue_id": "a-1", "status": "QUEUED"}
    )
    result = await async_client.audio.queue(
        model="a",
        prompt="a song",
        duration="30s",
    )
    assert result.queue_id == "a-1"
    assert result.status == "QUEUED"
    body = json.loads(route.calls.last.request.content)
    assert body == {"model": "a", "prompt": "a song", "duration": "30s"}


async def test_audio_retrieve_binary(mock_api, async_client):
    route = mock_api.post("/audio/retrieve").respond(200, content=b"MP3")
    result = await async_client.audio.retrieve_binary(
        model="a",
        queue_id="q",
        accept="audio/mpeg",
    )
    assert result == b"MP3"
    assert route.calls.last.request.headers["accept"] == "audio/mpeg"


async def test_audio_wait_returns_on_completed(mock_api, async_client):
    counter = {"n": 0}

    def handler(request):
        counter["n"] += 1
        status = "PROCESSING" if counter["n"] < 2 else "COMPLETED"
        return httpx.Response(200, json={"status": status})

    mock_api.post("/audio/retrieve").mock(side_effect=handler)
    result = await async_client.audio.wait_for_completion(
        model="a",
        queue_id="q",
        timeout_s=5.0,
        poll_interval_s=0.01,
    )
    assert result.status == "COMPLETED"


async def test_audio_wait_keeps_polling_on_lowercase_processing(mock_api, async_client):
    # A non-uppercase in-progress status must not look terminal and end the wait
    # mid-job; the loop keeps polling until a genuinely terminal status arrives.
    counter = {"n": 0}

    def handler(request):
        counter["n"] += 1
        status = "Processing" if counter["n"] < 2 else "COMPLETED"
        return httpx.Response(200, json={"status": status})

    mock_api.post("/audio/retrieve").mock(side_effect=handler)
    result = await async_client.audio.wait_for_completion(
        model="a", queue_id="q", timeout_s=5.0, poll_interval_s=0.01
    )
    assert result.status == "COMPLETED"
    assert counter["n"] == 2


async def test_audio_wait_raises_on_timeout(mock_api, async_client):
    def handler(request):
        return httpx.Response(200, json={"status": "PROCESSING"})

    mock_api.post("/audio/retrieve").mock(side_effect=handler)
    with pytest.raises(VeniceAudioTimeoutError):
        await async_client.audio.wait_for_completion(
            model="a",
            queue_id="q",
            timeout_s=0.05,
            poll_interval_s=0.01,
        )


async def test_audio_wait_returns_failed_status_by_default(mock_api, async_client):
    mock_api.post("/audio/retrieve").respond(200, json={"status": "FAILED"})
    result = await async_client.audio.wait_for_completion(
        model="a", queue_id="q", timeout_s=5.0, poll_interval_s=0.01
    )
    assert result.status == "FAILED"


async def test_audio_wait_raises_on_failed_when_opted_in(mock_api, async_client):
    mock_api.post("/audio/retrieve").respond(200, json={"status": "ERROR"})
    with pytest.raises(VeniceAudioFailedError) as info:
        await async_client.audio.wait_for_completion(
            model="a",
            queue_id="q",
            timeout_s=5.0,
            poll_interval_s=0.01,
            raise_on_failed=True,
        )
    assert info.value.queue_id == "q"
    assert info.value.status == "ERROR"
    assert info.value.result.status == "ERROR"


async def test_audio_wait_unknown_terminal_status_still_returns(mock_api, async_client):
    mock_api.post("/audio/retrieve").respond(200, json={"status": "DONE"})
    result = await async_client.audio.wait_for_completion(
        model="a",
        queue_id="q",
        timeout_s=5.0,
        poll_interval_s=0.01,
        raise_on_failed=True,
    )
    assert result.status == "DONE"


def test_sync_audio_wait_raises_on_failed_when_opted_in(mock_api, sync_client):
    mock_api.post("/audio/retrieve").respond(200, json={"status": "canceled"})
    with pytest.raises(VeniceAudioFailedError):
        sync_client.audio.wait_for_completion(
            model="a",
            queue_id="q",
            timeout_s=5.0,
            poll_interval_s=0.01,
            raise_on_failed=True,
        )


def test_sync_transcribe_accepts_file_like(mock_api, sync_client):
    route = mock_api.post("/audio/transcriptions").respond(200, json={"text": "ok"})
    handle = io.BytesIO(b"SYNCSTREAM")
    sync_client.audio.transcribe(file=handle, model="whisper-1")
    assert b"SYNCSTREAM" in route.calls.last.request.content
    assert not handle.closed


async def test_audio_quote(mock_api, async_client):
    # Swagger calls this "quote"; any extra fields Venice adds land on model_extra.
    mock_api.post("/audio/quote").respond(200, json={"quote": 0.1, "price": 0.1})
    result = await async_client.audio.quote(model="a", duration="30s")
    assert result.quote == 0.1
    assert result.model_extra == {"price": 0.1}


async def test_audio_complete(mock_api, async_client):
    route = mock_api.post("/audio/complete").respond(200, json={"ok": True})
    await async_client.audio.complete(model="a", queue_id="q")
    body = json.loads(route.calls.last.request.content)
    assert body == {"model": "a", "queue_id": "q"}
