"""Tests for the video resource, including the polling helper."""

from __future__ import annotations

import json

import pytest

from veniceresch import VeniceVideoTimeoutError


async def test_queue_posts_body(mock_api, async_client):
    route = mock_api.post("/video/queue").respond(
        200,
        json={"model": "v1", "queue_id": "q-123"},
    )
    result = await async_client.video.queue(
        model="v1",
        prompt="a cat",
        duration="5s",
        aspect_ratio="16:9",
    )
    assert result.queue_id == "q-123"
    assert result.model == "v1"
    body = json.loads(route.calls.last.request.content)
    assert body == {"model": "v1", "prompt": "a cat", "duration": "5s", "aspect_ratio": "16:9"}


async def test_retrieve_returns_status(mock_api, async_client):
    mock_api.post("/video/retrieve").respond(
        200,
        json={"status": "PROCESSING", "average_execution_time": 140000, "execution_duration": 5000},
    )
    result = await async_client.video.retrieve(model="v1", queue_id="q-123")
    assert result.status == "PROCESSING"
    assert result.average_execution_time == 140000
    assert result.execution_duration == 5000


async def test_retrieve_binary(mock_api, async_client):
    route = mock_api.post("/video/retrieve").respond(200, content=b"MP4DATA")
    result = await async_client.video.retrieve_binary(model="v1", queue_id="q-123")
    assert result == b"MP4DATA"
    assert route.calls.last.request.headers["accept"] == "video/mp4"


async def test_quote(mock_api, async_client):
    # Swagger calls this field "quote"; test uses the name Venice returns.
    # Any additional fields Venice adds (e.g. price_usd) land on model_extra.
    mock_api.post("/video/quote").respond(200, json={"quote": 0.05, "price_usd": 0.05})
    result = await async_client.video.quote(model="v1", duration="5s")
    assert result.quote == 0.05
    assert result.model_extra == {"price_usd": 0.05}


async def test_complete(mock_api, async_client):
    route = mock_api.post("/video/complete").respond(200, json={"ok": True})
    await async_client.video.complete(model="v1", queue_id="q-123")
    body = json.loads(route.calls.last.request.content)
    assert body == {"model": "v1", "queue_id": "q-123"}


async def test_transcribe(mock_api, async_client):
    route = mock_api.post("/video/transcriptions").respond(
        200, json={"transcript": "hello", "lang": "en"}
    )
    result = await async_client.video.transcribe(
        url="https://youtube.com/watch?v=x", response_format="json"
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "url": "https://youtube.com/watch?v=x",
        "response_format": "json",
    }
    assert result.transcript == "hello"
    assert result.lang == "en"


# ---- wait_for_completion --------------------------------------------------


async def test_wait_returns_on_completed(async_client, mock_api):
    import httpx

    request_list = []

    def handler(request):
        request_list.append(request)
        if len(request_list) < 3:
            body = {"status": "PROCESSING", "average_execution_time": 1, "execution_duration": 1}
        else:
            body = {"status": "COMPLETED", "average_execution_time": 1, "execution_duration": 1}
        return httpx.Response(200, json=body)

    mock_api.post("/video/retrieve").mock(side_effect=handler)
    result = await async_client.video.wait_for_completion(
        model="v1",
        queue_id="q-123",
        timeout_s=5.0,
        poll_interval_s=0.01,
    )
    assert result.status == "COMPLETED"
    assert len(request_list) == 3


async def test_wait_raises_on_timeout(async_client, mock_api):
    import httpx

    def handler(request):
        return httpx.Response(
            200,
            json={"status": "PROCESSING", "average_execution_time": 1, "execution_duration": 1},
        )

    mock_api.post("/video/retrieve").mock(side_effect=handler)
    with pytest.raises(VeniceVideoTimeoutError) as info:
        await async_client.video.wait_for_completion(
            model="v1",
            queue_id="q-timeout",
            timeout_s=0.05,
            poll_interval_s=0.01,
        )
    assert info.value.queue_id == "q-timeout"


def test_sync_video_queue(mock_api, sync_client):
    mock_api.post("/video/queue").respond(200, json={"model": "v1", "queue_id": "q"})
    result = sync_client.video.queue(model="v1", prompt="p", duration="5s")
    assert result.queue_id == "q"
