"""Tests for the audio resource."""

from __future__ import annotations

import json

import httpx
import pytest

from veniceresch import VeniceAudioTimeoutError


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
