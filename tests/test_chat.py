"""Tests for the chat resource: create and stream."""

from __future__ import annotations

import json

import pytest

from veniceresch import AsyncVeniceClient

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
    assert result.id == "cmpl-1"
    assert result.choices[0]["message"]["content"] == "hi"
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


async def test_response_tolerates_unknown_fields(mock_api, async_client):
    # Venice adds fields frequently; the client must not raise on them.
    # Known fields are accessible as attributes; unknown fields land in
    # model_extra via ConfigDict(extra="allow") on VeniceBaseModel.
    mock_api.post("/chat/completions").respond(
        200,
        json={
            "id": "x",
            "choices": [],
            "brand_new_venice_field": {"shipped_today": True},
        },
    )
    result = await async_client.chat.create(model="m", messages=[{"role": "user", "content": "h"}])
    assert result.id == "x"
    assert result.model_extra == {"brand_new_venice_field": {"shipped_today": True}}


async def test_create_drops_none_extras(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(200, json={"id": "x"})
    await async_client.chat.create(
        model="m",
        messages=[{"role": "user", "content": "h"}],
        temperature=None,  # explicit None should be dropped
    )
    body = json.loads(route.calls.last.request.content)
    assert "temperature" not in body


async def test_create_stream_true_returns_iterator(mock_api, async_client):
    # stream=True returns an async iterator of ChatCompletionChunk. Requires
    # await before async for — same contract as OpenAI's SDK.
    sse_body = b'data: {"id":"a"}\n\ndata: {"id":"b"}\n\ndata: [DONE]\n\n'
    mock_api.post("/chat/completions").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    stream = await async_client.chat.create(
        model="m", messages=[{"role": "user", "content": "h"}], stream=True
    )
    events = [event async for event in stream]
    assert [e.id for e in events] == ["a", "b"]


async def test_create_stream_true_matches_stream_method(mock_api, async_client):
    # create(stream=True) and stream() should decode the same events.
    sse_body = b'data: {"id":"a"}\n\ndata: {"id":"b"}\n\ndata: [DONE]\n\n'
    mock_api.post("/chat/completions").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    via_create = [
        event
        async for event in await async_client.chat.create(
            model="m", messages=[{"role": "user", "content": "h"}], stream=True
        )
    ]

    mock_api.post("/chat/completions").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    via_stream = [
        event
        async for event in await async_client.chat.stream(
            model="m", messages=[{"role": "user", "content": "h"}]
        )
    ]
    assert [e.id for e in via_create] == [e.id for e in via_stream] == ["a", "b"]


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
    stream = await async_client.chat.stream(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
    )
    async for event in stream:
        events.append(event)
    assert len(events) == 2
    assert events[0].choices[0]["delta"]["content"] == "He"
    assert events[1].choices[0]["delta"]["content"] == "llo"


async def test_stream_sends_stream_true(mock_api, async_client):
    route = mock_api.post("/chat/completions").respond(
        200,
        content=b"data: [DONE]\n\n",
        headers={"content-type": "text/event-stream"},
    )
    async for _ in await async_client.chat.stream(
        model="m",
        messages=[{"role": "user", "content": "h"}],
    ):
        pass
    body = json.loads(route.calls.last.request.content)
    assert body["stream"] is True


async def test_stream_raises_error_before_yielding(mock_api, async_client):
    from veniceresch import VeniceRateLimitError

    mock_api.post("/chat/completions").respond(429, json={"error": "slow"})
    with pytest.raises(VeniceRateLimitError):
        stream = await async_client.chat.stream(
            model="m",
            messages=[{"role": "user", "content": "h"}],
        )
        async for _ in stream:
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
    stream = await async_client.chat.stream(
        model="m",
        messages=[{"role": "user", "content": "h"}],
    )
    async for event in stream:
        events.append(event)
    assert [e.id for e in events] == ["a", "b"]


async def test_stream_ignores_comments_and_unknown_fields(mock_api, async_client):
    body = b': keepalive\n\nevent: whatever\nid: 1\ndata: {"n":42}\n\ndata: [DONE]\n\n'
    mock_api.post("/chat/completions").respond(
        200,
        content=body,
        headers={"content-type": "text/event-stream"},
    )
    stream = await async_client.chat.stream(
        model="m",
        messages=[{"role": "user", "content": "h"}],
    )
    events = [e async for e in stream]
    assert len(events) == 1
    # "n":42 arrives as an extra field thanks to extra=allow on the base model.
    assert events[0].model_extra == {"n": 42}


# ---- sync client also has .chat ------------------------------------------


def test_sync_create(mock_api, sync_client):
    mock_api.post("/chat/completions").respond(200, json={"id": "x"})
    result = sync_client.chat.create(
        model="m",
        messages=[{"role": "user", "content": "h"}],
    )
    assert result.id == "x"


def test_sync_stream(mock_api, sync_client):
    mock_api.post("/chat/completions").respond(
        200,
        content=b'data: {"id":"s1"}\n\ndata: [DONE]\n\n',
        headers={"content-type": "text/event-stream"},
    )
    events = list(
        sync_client.chat.stream(
            model="m",
            messages=[{"role": "user", "content": "h"}],
        )
    )
    assert [e.id for e in events] == ["s1"]


# ---- chat resource available via attribute on client ---------------------


def test_chat_attribute_exists():
    c = AsyncVeniceClient(api_key="k")
    from veniceresch.resources.chat import AsyncChatResource

    assert isinstance(c.chat, AsyncChatResource)


# ---- OpenAI-compat chat.completions namespace alias ----------------------


async def test_completions_create_matches_chat_create(mock_api, async_client):
    # chat.create(...) and chat.completions.create(...) must produce identical
    # HTTP requests (same path, body) and identical responses.
    async def _one_shot() -> tuple[dict, dict]:
        route = mock_api.post("/chat/completions").respond(200, json={"id": "x", "n": 1})
        result = await async_client.chat.completions.create(
            model="m", messages=[{"role": "user", "content": "h"}]
        )
        body = json.loads(route.calls.last.request.content)
        mock_api.reset()
        return result, body

    via_completions, body_completions = await _one_shot()

    route = mock_api.post("/chat/completions").respond(200, json={"id": "x", "n": 1})
    via_chat = await async_client.chat.create(
        model="m", messages=[{"role": "user", "content": "h"}]
    )
    body_chat = json.loads(route.calls.last.request.content)

    assert via_completions.id == via_chat.id == "x"
    assert body_completions == body_chat


async def test_completions_stream_matches_chat_stream(mock_api, async_client):
    sse_body = b'data: {"id":"ev"}\n\ndata: [DONE]\n\n'
    mock_api.post("/chat/completions").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    via_completions = [
        e.id
        async for e in await async_client.chat.completions.stream(
            model="m", messages=[{"role": "user", "content": "h"}]
        )
    ]

    mock_api.post("/chat/completions").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    via_chat = [
        e.id
        async for e in await async_client.chat.stream(
            model="m", messages=[{"role": "user", "content": "h"}]
        )
    ]
    assert via_completions == via_chat == ["ev"]


async def test_completions_create_stream_true(mock_api, async_client):
    sse_body = b'data: {"id":"ev2"}\n\ndata: [DONE]\n\n'
    mock_api.post("/chat/completions").respond(
        200, content=sse_body, headers={"content-type": "text/event-stream"}
    )
    stream = await async_client.chat.completions.create(
        model="m", messages=[{"role": "user", "content": "h"}], stream=True
    )
    events = [e async for e in stream]
    assert [e.id for e in events] == ["ev2"]


def test_sync_completions_create(mock_api, sync_client):
    mock_api.post("/chat/completions").respond(200, json={"id": "sx"})
    result = sync_client.chat.completions.create(
        model="m", messages=[{"role": "user", "content": "h"}]
    )
    assert result.id == "sx"


def test_sync_completions_stream_true(mock_api, sync_client):
    mock_api.post("/chat/completions").respond(
        200,
        content=b'data: {"id":"s3"}\n\ndata: [DONE]\n\n',
        headers={"content-type": "text/event-stream"},
    )
    events = list(
        sync_client.chat.completions.create(
            model="m", messages=[{"role": "user", "content": "h"}], stream=True
        )
    )
    assert [e.id for e in events] == ["s3"]
