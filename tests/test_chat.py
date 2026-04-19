"""Tests for the chat resource: create, stream, create_response."""

from __future__ import annotations

import json

import pytest

from venice_sdk import AsyncVeniceClient

# ---- non-streaming --------------------------------------------------------


async def test_create_posts_to_chat_completions(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(
        200,
        json={
            "id": "cmpl-1",
            "choices": [{"message": {"role": "assistant", "content": "hi"}}],
        },
    )
    result = await async_client.chat.create(
        model="llama-3.3-70b",
        messages=[{"role": "user", "content": "hello"}],
    )
    assert result["id"] == "cmpl-1"
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "model": "llama-3.3-70b",
        "messages": [{"role": "user", "content": "hello"}],
    }


async def test_create_forwards_venice_parameters(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(200, json={"id": "x"})
    await async_client.chat.create(
        model="m",
        messages=[{"role": "user", "content": "h"}],
        venice_parameters={"include_venice_system_prompt": False, "character_slug": "bob"},
    )
    body = json.loads(route.calls.last.request.content)
    assert body["venice_parameters"] == {
        "include_venice_system_prompt": False,
        "character_slug": "bob",
    }


async def test_create_forwards_openai_compatible_fields(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(200, json={"id": "x"})
    await async_client.chat.create(
        model="m",
        messages=[{"role": "user", "content": "h"}],
        temperature=0.7,
        max_tokens=512,
        tools=[{"type": "function", "function": {"name": "get_time"}}],
    )
    body = json.loads(route.calls.last.request.content)
    assert body["temperature"] == 0.7
    assert body["max_tokens"] == 512
    assert body["tools"][0]["function"]["name"] == "get_time"
    assert "stream" not in body  # non-streaming


async def test_create_drops_none_extras(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(200, json={"id": "x"})
    await async_client.chat.create(
        model="m",
        messages=[{"role": "user", "content": "h"}],
        temperature=None,  # explicit None should be dropped
    )
    body = json.loads(route.calls.last.request.content)
    assert "temperature" not in body


async def test_create_rejects_stream_kwarg(async_client):
    with pytest.raises(ValueError, match="stream=True"):
        await async_client.chat.create(
            model="m",
            messages=[{"role": "user", "content": "h"}],
            stream=True,
        )


async def test_create_supports_vision_and_audio_parts(mock_api, async_client):
    # ChatCompletionContentPartVideoUrl + ChatCompletionContentPartInputAudio
    # are the Venice-specific content parts from the plan. We just pass them
    # through untouched.
    route = mock_api.post("/chat/completions").respond(200, json={"id": "x"})
    multimodal_content = [
        {"type": "text", "text": "describe this"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        {"type": "video_url", "video_url": {"url": "https://x/v.mp4"}},
        {"type": "input_audio", "input_audio": {"data": "...", "format": "wav"}},
    ]
    await async_client.chat.create(
        model="m",
        messages=[{"role": "user", "content": multimodal_content}],
    )
    body = json.loads(route.calls.last.request.content)
    assert body["messages"][0]["content"] == multimodal_content


# ---- streaming ------------------------------------------------------------


async def test_stream_parses_sse_events(mock_api, async_client):
    sse_body = (
        b'data: {"id":"x","choices":[{"delta":{"content":"He"}}]}\n\n'
        b'data: {"id":"x","choices":[{"delta":{"content":"llo"}}]}\n\n'
        b"data: [DONE]\n\n"
    )
    mock_api.post("/chat/completions").respond(
        200,
        content=sse_body,
        headers={"content-type": "text/event-stream"},
    )
    events = []
    async for event in async_client.chat.stream(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
    ):
        events.append(event)
    assert len(events) == 2
    assert events[0]["choices"][0]["delta"]["content"] == "He"
    assert events[1]["choices"][0]["delta"]["content"] == "llo"


async def test_stream_sends_stream_true(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(
        200,
        content=b"data: [DONE]\n\n",
        headers={"content-type": "text/event-stream"},
    )
    async for _ in async_client.chat.stream(
        model="m",
        messages=[{"role": "user", "content": "h"}],
    ):
        pass
    body = json.loads(route.calls.last.request.content)
    assert body["stream"] is True


async def test_stream_raises_error_before_yielding(mock_api, async_client):
    from venice_sdk import VeniceRateLimitError

    mock_api.post("/chat/completions").respond(429, json={"error": "slow"})
    with pytest.raises(VeniceRateLimitError):
        async for _ in async_client.chat.stream(
            model="m",
            messages=[{"role": "user", "content": "h"}],
        ):
            pass  # pragma: no cover


async def test_stream_handles_split_chunks(mock_api, async_client):
    # httpx may deliver the stream in arbitrary chunk boundaries — the parser
    # must not lose events that straddle a chunk.
    full = b'data: {"id":"a","n":1}\n\ndata: {"id":"b","n":2}\n\ndata: [DONE]\n\n'
    mock_api.post("/chat/completions").respond(
        200,
        content=full,
        headers={"content-type": "text/event-stream"},
    )
    events = []
    async for event in async_client.chat.stream(
        model="m",
        messages=[{"role": "user", "content": "h"}],
    ):
        events.append(event)
    assert [e["n"] for e in events] == [1, 2]


async def test_stream_ignores_comments_and_unknown_fields(mock_api, async_client):
    body = b': keepalive\n\nevent: whatever\nid: 1\ndata: {"n":42}\n\ndata: [DONE]\n\n'
    mock_api.post("/chat/completions").respond(
        200,
        content=body,
        headers={"content-type": "text/event-stream"},
    )
    events = [
        e
        async for e in async_client.chat.stream(
            model="m",
            messages=[{"role": "user", "content": "h"}],
        )
    ]
    assert events == [{"n": 42}]


# ---- /responses endpoint --------------------------------------------------


async def test_create_response(mock_api, async_client):
    route = mock_api.post("/responses").respond(200, json={"id": "resp-1", "output": "hello"})
    result = await async_client.chat.create_response(
        model="m",
        input=[{"role": "user", "content": "hi"}],
    )
    assert result["id"] == "resp-1"
    body = json.loads(route.calls.last.request.content)
    assert body["model"] == "m"
    assert body["input"] == [{"role": "user", "content": "hi"}]


# ---- sync client also has .chat ------------------------------------------


def test_sync_create(mock_api, sync_client):
    mock_api.post("/chat/completions").respond(200, json={"id": "x"})
    result = sync_client.chat.create(
        model="m",
        messages=[{"role": "user", "content": "h"}],
    )
    assert result["id"] == "x"


def test_sync_stream(mock_api, sync_client):
    mock_api.post("/chat/completions").respond(
        200,
        content=b'data: {"n":1}\n\ndata: [DONE]\n\n',
        headers={"content-type": "text/event-stream"},
    )
    events = list(
        sync_client.chat.stream(
            model="m",
            messages=[{"role": "user", "content": "h"}],
        )
    )
    assert events == [{"n": 1}]


# ---- chat resource available via attribute on client ---------------------


def test_chat_attribute_exists():
    c = AsyncVeniceClient(api_key="k")
    from venice_sdk.resources.chat import AsyncChatResource

    assert isinstance(c.chat, AsyncChatResource)
