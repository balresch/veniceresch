"""Tests for the video resource, including the polling helper."""

from __future__ import annotations

import json

import httpx
import pytest

from veniceresch import VeniceUnexpectedContentTypeError, VeniceVideoTimeoutError

# JSON status blob a VPS-backed model returns from /video/retrieve instead of
# MP4 bytes — the shape that bit the lewdresch/DIEMshare integration.
_VPS_STATUS = {
    "status": "COMPLETED",
    "average_execution_time": 239075,
    "execution_duration": 26097,
    "download_url": "https://cdn.venice.ai/videos/q-123.mp4",
}


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


async def test_retrieve_binary_raises_on_json_body(mock_api, async_client):
    # VPS-backed models answer the Accept: video/mp4 call with a JSON status
    # object. That must NOT be returned verbatim as "MP4 bytes".
    mock_api.post("/video/retrieve").respond(200, json=_VPS_STATUS)
    with pytest.raises(VeniceUnexpectedContentTypeError) as info:
        await async_client.video.retrieve_binary(model="v1", queue_id="q-123")
    assert info.value.content_type.startswith("application/json")
    assert info.value.error_body["download_url"] == _VPS_STATUS["download_url"]


@pytest.mark.parametrize(
    "content_type",
    ["text/html", "text/plain", "application/xml", "application/xhtml+xml"],
)
async def test_retrieve_binary_raises_on_textual_body(mock_api, async_client, content_type):
    # A 2xx textual body (CDN error page, auth-proxy interstitial, presigned-URL
    # error) is the same silent-corruption class as the JSON case and must not be
    # returned verbatim as "MP4 bytes".
    mock_api.post("/video/retrieve").respond(
        200, content=b"<html>nope</html>", headers={"content-type": content_type}
    )
    with pytest.raises(VeniceUnexpectedContentTypeError) as info:
        await async_client.video.retrieve_binary(model="v1", queue_id="q-123")
    assert info.value.content_type == content_type


def test_sync_retrieve_binary_raises_on_textual_body(mock_api, sync_client):
    mock_api.post("/video/retrieve").respond(
        200, content=b"oops", headers={"content-type": "text/plain"}
    )
    with pytest.raises(VeniceUnexpectedContentTypeError):
        sync_client.video.retrieve_binary(model="v1", queue_id="q-123")


async def test_retrieve_binary_passes_untyped_body(mock_api, async_client):
    # No content-type header → cannot tell, so the bytes pass through unchanged.
    route = mock_api.post("/video/retrieve").respond(200, content=b"RAWBYTES")
    route.return_value.headers.pop("content-type", None)
    result = await async_client.video.retrieve_binary(model="v1", queue_id="q-123")
    assert result == b"RAWBYTES"


@pytest.mark.parametrize(
    "content_type",
    ["video/mp4", "image/png", "audio/mpeg", "application/octet-stream"],
)
async def test_retrieve_binary_passes_real_media(mock_api, async_client, content_type):
    mock_api.post("/video/retrieve").respond(
        200, content=b"MEDIA", headers={"content-type": content_type}
    )
    result = await async_client.video.retrieve_binary(model="v1", queue_id="q-123")
    assert result == b"MEDIA"


async def test_download_direct_bytes_model(mock_api, async_client):
    # Direct-bytes model: one call, MP4 bytes straight back.
    route = mock_api.post("/video/retrieve").respond(200, content=b"MP4DATA")
    result = await async_client.video.download(model="v1", queue_id="q-123")
    assert result == b"MP4DATA"
    assert route.call_count == 1


async def test_download_vps_model_follows_download_url(mock_api, async_client):
    mock_api.post("/video/retrieve").respond(200, json=_VPS_STATUS)
    cdn = mock_api.get(_VPS_STATUS["download_url"]).respond(200, content=b"REALMP4")
    result = await async_client.video.download(model="v1", queue_id="q-123")
    assert result == b"REALMP4"
    # The CDN URL is presigned — the Venice bearer must not be forwarded.
    assert "authorization" not in cdn.calls.last.request.headers


async def test_download_explicit_url_skips_retrieve(mock_api, async_client):
    # VPS-backed models: the only handle to the media is the queue submit's
    # download_url. Passing it fetches directly, never touching /video/retrieve.
    retrieve = mock_api.post("/video/retrieve")
    cdn = mock_api.get(_VPS_STATUS["download_url"]).respond(200, content=b"REALMP4")
    result = await async_client.video.download(
        model="v1", queue_id="q-123", download_url=_VPS_STATUS["download_url"]
    )
    assert result == b"REALMP4"
    assert retrieve.call_count == 0
    # Presigned URL — the Venice bearer must not be forwarded.
    assert "authorization" not in cdn.calls.last.request.headers


def test_sync_download_explicit_url_skips_retrieve(mock_api, sync_client):
    retrieve = mock_api.post("/video/retrieve")
    mock_api.get(_VPS_STATUS["download_url"]).respond(200, content=b"REALMP4")
    result = sync_client.video.download(
        model="v1", queue_id="q-123", download_url=_VPS_STATUS["download_url"]
    )
    assert result == b"REALMP4"
    assert retrieve.call_count == 0


async def test_download_reraises_when_no_download_url(mock_api, async_client):
    mock_api.post("/video/retrieve").respond(
        200, json={"status": "COMPLETED", "execution_duration": 1}
    )
    with pytest.raises(VeniceUnexpectedContentTypeError):
        await async_client.video.download(model="v1", queue_id="q-123")


def test_sync_download_vps_model(mock_api, sync_client):
    mock_api.post("/video/retrieve").respond(200, json=_VPS_STATUS)
    mock_api.get(_VPS_STATUS["download_url"]).respond(200, content=b"REALMP4")
    assert sync_client.video.download(model="v1", queue_id="q-123") == b"REALMP4"


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
