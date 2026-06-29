"""Sync/async wire-parity tests (backlog item #6 / review #2).

Resources mirror their async and sync surfaces line-for-line by deliberate
design (CLAUDE.md: "Two distinct layers; they must stay distinct"). The risk
that buys is *drift*: a bug fix or parameter-translation change landing in only
one of the two mirrors.

These tests guard the methods with **non-trivial** behavior — parameter
translation (``model_id`` → ``modelId``, snake_case → camelCase), wallet-auth
header / ``no_auth`` handling, multipart body shaping, ``return_binary``
forcing, and extras stringification. For each, the *same* inputs are sent
through the async and the sync method against the *same* respx mock, and the two
outgoing HTTP requests are asserted byte-for-byte identical (URL, headers,
body). Trivial post-and-parse methods are intentionally not covered here.
"""

from __future__ import annotations

from typing import Any

import httpx


def _fingerprint(request: httpx.Request) -> dict[str, Any]:
    """Normalize an outgoing request to a comparable shape.

    Multipart bodies carry a per-request random boundary (in both the
    ``Content-Type`` header and the body itself); httpx always uses a
    fixed-length boundary, so content-length is stable, but the boundary bytes
    differ between two otherwise-identical requests. We replace the boundary
    with a placeholder so the comparison reflects the actual field content.
    """
    ctype = request.headers.get("content-type", "")
    content = request.content
    headers = dict(request.headers)
    if "multipart/form-data" in ctype and "boundary=" in ctype:
        boundary = ctype.split("boundary=", 1)[1]
        content = content.replace(boundary.encode(), b"BOUNDARY")
        headers["content-type"] = "multipart/form-data; boundary=BOUNDARY"
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": headers,
        "content": content,
    }


def _assert_parity(route: Any) -> dict[str, Any]:
    """Assert the route's two recorded requests (async then sync) are identical."""
    assert len(route.calls) == 2, f"expected exactly 2 calls, got {len(route.calls)}"
    async_fp = _fingerprint(route.calls[0].request)
    sync_fp = _fingerprint(route.calls[1].request)
    assert async_fp == sync_fp
    return async_fp


# ---- image: model_id → modelId translation + image list encoding ----------


async def test_multi_edit_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/image/multi-edit").respond(200, content=b"PNG")
    kwargs = dict(
        images=[b"\x89PNG-one", b"\x89PNG-two"],
        prompt="merge",
        model_id="flux-multi",
        strength=0.7,
    )
    await async_client.image.multi_edit(**kwargs)
    sync_client.image.multi_edit(**kwargs)
    fp = _assert_parity(route)
    # The camelCase translation must be on the wire identically for both.
    assert b'"modelId"' in fp["content"]
    assert b'"model_id"' not in fp["content"]


# ---- image: return_binary forcing on generate / generate_binary -----------


async def test_generate_drops_return_binary_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/image/generate").respond(200, json={"images": []})
    kwargs = dict(model="m", prompt="p", return_binary=True)
    await async_client.image.generate(**kwargs)
    sync_client.image.generate(**kwargs)
    fp = _assert_parity(route)
    assert b"return_binary" not in fp["content"]


async def test_generate_binary_forces_return_binary_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/image/generate").respond(200, content=b"PNG")
    kwargs = dict(model="m", prompt="p")
    await async_client.image.generate_binary(**kwargs)
    sync_client.image.generate_binary(**kwargs)
    fp = _assert_parity(route)
    assert b'"return_binary":true' in fp["content"].replace(b" ", b"")


# ---- audio: multipart upload + default bearer auth ------------------------


async def test_create_cloned_voice_multipart_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/audio/voices").respond(200, json={"id": "vv_1", "model": "tts"})
    kwargs = dict(file=b"AUDIOSAMPLE", model="tts-chatterbox-hd")
    await async_client.audio.create_cloned_voice(**kwargs)
    sync_client.audio.create_cloned_voice(**kwargs)
    fp = _assert_parity(route)
    assert fp["headers"]["authorization"].startswith("Bearer ")


# ---- audio: path upload — async reads to bytes off-thread, sync streams ---


async def test_create_cloned_voice_path_parity(mock_api, async_client, sync_client, tmp_path):
    # A filesystem path takes different in-process routes on each surface
    # (item #13): async reads it to bytes via asyncio.to_thread, sync streams an
    # open handle. The multipart body on the wire must still be byte-identical.
    route = mock_api.post("/audio/voices").respond(200, json={"id": "vv_3", "model": "tts"})
    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"WAVE-SAMPLE-BYTES")
    await async_client.audio.create_cloned_voice(file=sample, model="tts")
    sync_client.audio.create_cloned_voice(file=sample, model="tts")
    fp = _assert_parity(route)
    assert b'filename="sample.wav"' in fp["content"]
    assert b"WAVE-SAMPLE-BYTES" in fp["content"]


# ---- audio: wallet auth strips bearer + sets SIGN-IN-WITH-X ---------------


async def test_create_cloned_voice_siwx_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/audio/voices").respond(200, json={"id": "vv_2", "model": "tts"})
    kwargs = dict(file=b"AUDIOSAMPLE", model="tts", siwx_header="siwx-payload")
    await async_client.audio.create_cloned_voice(**kwargs)
    sync_client.audio.create_cloned_voice(**kwargs)
    fp = _assert_parity(route)
    assert fp["headers"]["sign-in-with-x"] == "siwx-payload"
    assert "authorization" not in fp["headers"]


# ---- audio: multipart form extras stringified ----------------------------


async def test_transcribe_extras_stringified_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/audio/transcriptions").respond(200, json={"text": "hi"})
    kwargs = dict(file=b"CLIP", model="whisper", response_format="json", temperature=0.0)
    await async_client.audio.transcribe(**kwargs)
    sync_client.audio.transcribe(**kwargs)
    fp = _assert_parity(route)
    # Non-str extras are coerced to str for the multipart form on both surfaces.
    assert b'name="temperature"' in fp["content"]


# ---- audio: Accept header override on binary retrieve --------------------


async def test_retrieve_binary_accept_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/audio/retrieve").respond(200, content=b"MP3")
    kwargs = dict(model="a", queue_id="a-1", accept="audio/wav")
    await async_client.audio.retrieve_binary(**kwargs)
    sync_client.audio.retrieve_binary(**kwargs)
    fp = _assert_parity(route)
    assert fp["headers"]["accept"] == "audio/wav"


# ---- chat: venice_parameters + promoted-kwarg merge ----------------------


async def test_chat_create_venice_parameters_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/chat/completions").respond(200, json={"id": "c1", "choices": []})
    kwargs = dict(
        model="venice-uncensored",
        messages=[{"role": "user", "content": "hi"}],
        venice_parameters={"include_venice_system_prompt": False},
        temperature=0.5,
        top_p=0.9,
        seed=7,
        repetition_penalty=1.1,  # forwarded via **extra
    )
    await async_client.chat.create(**kwargs)
    sync_client.chat.create(**kwargs)
    fp = _assert_parity(route)
    assert b"venice_parameters" in fp["content"]
    assert b"repetition_penalty" in fp["content"]


async def test_chat_stream_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/chat/completions").respond(200, content=b"data: [DONE]\n\n")
    kwargs = dict(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        venice_parameters={"foo": "bar"},
        temperature=0.2,
    )
    async for _ in await async_client.chat.stream(**kwargs):
        pass
    for _ in sync_client.chat.stream(**kwargs):
        pass
    fp = _assert_parity(route)
    assert fp["headers"]["accept"] == "text/event-stream"
    assert b'"stream":true' in fp["content"].replace(b" ", b"")


# ---- x402: wallet-auth GET with path param + no_auth ---------------------


async def test_x402_balance_parity(mock_api, async_client, sync_client):
    route = mock_api.get("/x402/balance/0xWALLET").respond(200, json={"balance": "0"})
    kwargs = dict(siwx_header="siwe-payload")
    await async_client.x402.balance("0xWALLET", **kwargs)
    sync_client.x402.balance("0xWALLET", **kwargs)
    fp = _assert_parity(route)
    # Legacy X-Sign-In-With-X header for x402; default bearer stripped.
    assert fp["headers"]["x-sign-in-with-x"] == "siwe-payload"
    assert "authorization" not in fp["headers"]


async def test_x402_top_up_payment_header_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/x402/top-up").respond(200, json={"success": True})
    kwargs = dict(payment_header="signed-x402-payload")
    await async_client.x402.top_up(**kwargs)
    sync_client.x402.top_up(**kwargs)
    fp = _assert_parity(route)
    assert fp["headers"]["x-402-payment"] == "signed-x402-payload"
    assert "authorization" not in fp["headers"]


# ---- crypto: batch JSON-RPC body + wallet auth + idempotency -------------


async def test_crypto_rpc_batch_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/crypto/rpc/base").respond(200, json=[{"id": 1, "result": "0x1"}])
    request_body = [
        {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
        {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 2},
    ]
    kwargs = dict(siwx_header="siwx-payload", idempotency_key="idem-1")
    await async_client.crypto.rpc("base", request_body, **kwargs)
    sync_client.crypto.rpc("base", request_body, **kwargs)
    fp = _assert_parity(route)
    assert fp["headers"]["sign-in-with-x"] == "siwx-payload"
    assert fp["headers"]["idempotency-key"] == "idem-1"
    assert "authorization" not in fp["headers"]


# ---- api_keys: camelCase body translation --------------------------------


async def test_api_keys_create_camelcase_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/api_keys").respond(200, json={"data": {}})
    kwargs = dict(
        api_key_type="INFERENCE",
        description="key",
        consumption_limit={"usd": 10},
        expires_at="2027-01-01",
    )
    await async_client.api_keys.create(**kwargs)
    sync_client.api_keys.create(**kwargs)
    fp = _assert_parity(route)
    for camel in (b"apiKeyType", b"consumptionLimit", b"expiresAt"):
        assert camel in fp["content"]


# ---- api_keys: web3 key mint strips bearer (no_auth) ---------------------


async def test_generate_web3_key_no_auth_parity(mock_api, async_client, sync_client):
    route = mock_api.post("/api_keys/generate_web3_key").respond(200, json={"data": {}})
    kwargs = dict(
        api_key_type="INFERENCE",
        address="0xADDR",
        signature="0xSIG",
        token="challenge-token",
    )
    await async_client.api_keys.generate_web3_key(**kwargs)
    sync_client.api_keys.generate_web3_key(**kwargs)
    fp = _assert_parity(route)
    assert "authorization" not in fp["headers"]
    assert b"apiKeyType" in fp["content"]
