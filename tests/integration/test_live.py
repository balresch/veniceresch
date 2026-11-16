"""Integration smoke tests — these hit the real Venice API.

Run with ``VENICE_API_KEY=... pytest tests/integration -m integration``.
Skipped by default (no key). This is a smoke, not a regression suite: it
exists to catch upstream drift the respx-mocked unit suite cannot see (wire
shapes, content types, headers, status codes).

Cost tiers:

* **Free / token-cheap** (always run when a key is set): read-only billing and
  model calls, price quotes, the retired-endpoint 410 checks, and a
  single-question ``/decisions`` call of a few tokens (same order of cost as the
  minimal chat test).
* **Admin-only** (opt-in with ``VENICE_ADMIN_API_KEY``): ``/billing/*``
  rejects inference keys with 401, so those tests use a separate admin key and
  skip without it — the routine key can stay a limited inference key.
* **Paid** (opt-in with ``VENICE_INTEGRATION_PAID=1``): flows that are billed
  per job — e.g. the voice-changer round trip, which Venice charges by the
  minute (rounded up), plus the TTS call that produces its source clip. The
  weekly scheduled CI run leaves this off; trigger it manually with the
  workflow's ``paid`` input.
"""

from __future__ import annotations

import os
import struct
import zlib
from pathlib import Path
from typing import Any

import pytest

from veniceresch import AsyncVeniceClient, VeniceGoneError, text_deltas
from veniceresch.types import (
    BillingBalanceResponse,
    BillingUsageHistoryCsvPage,
    BillingUsageHistoryResponse,
    ChatCompletionResponse,
    DecisionResponse,
    GenerateImageResponse,
    ImageBytes,
    ImageStylesResponse,
    ModelList,
    VoiceChangerQuoteResponse,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def api_key() -> str:
    key = os.environ.get("VENICE_API_KEY")
    if not key:
        pytest.skip("VENICE_API_KEY not set — integration tests disabled.")
    return key


@pytest.fixture(scope="module")
def admin_key() -> str:
    """Admin-scope key for /billing/* and other admin-only routes.

    Kept separate from ``VENICE_API_KEY`` so the routine smoke can run on a
    tightly limited *inference* key; Venice answers admin routes with
    401 "Admin API key required" for inference keys.
    """
    key = os.environ.get("VENICE_ADMIN_API_KEY")
    if not key:
        pytest.skip("VENICE_ADMIN_API_KEY not set — admin-only (billing) tests disabled.")
    return key


@pytest.fixture
def paid(api_key: str) -> str:
    """Gate for tests that incur real per-job charges."""
    if os.environ.get("VENICE_INTEGRATION_PAID") != "1":
        pytest.skip("Paid integration test — set VENICE_INTEGRATION_PAID=1 to run.")
    return api_key


def _spec(model: dict[str, Any]) -> dict[str, Any]:
    spec = model.get("model_spec")
    return spec if isinstance(spec, dict) else {}


async def _voice_changer_model(client: AsyncVeniceClient) -> dict[str, Any]:
    models = await client.models.list(type="all")
    for model in models.data:
        if _spec(model).get("voice_changer"):
            return model
    pytest.skip("No voice-changer model available on this account.")


# ---- existing smoke -----------------------------------------------------------


async def test_models_list(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.models.list()
        assert isinstance(result, ModelList)
        assert isinstance(result.data, list)


async def test_models_list_video(api_key: str) -> None:
    """The ``type`` kwarg is a plain str; any value Venice accepts works end-to-end."""
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.models.list(type="video")
        assert isinstance(result, ModelList)


async def test_billing_balance(admin_key: str) -> None:
    async with AsyncVeniceClient(api_key=admin_key) as client:
        result = await client.billing.balance()
        assert isinstance(result, BillingBalanceResponse)


async def test_chat_completion_minimal(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        models = await client.models.list(type="text")
        if not models.data:
            pytest.skip("No text models available on this account.")
        # Prefer a non-reasoning model: a reasoning model can spend the whole
        # tiny max_tokens budget on reasoning_content and return content=None.
        plain = [
            m
            for m in models.data
            if not (_spec(m).get("capabilities") or {}).get("supportsReasoning")
        ]
        model_id = (plain or models.data)[0]["id"]
        result = await client.chat.create(
            model=model_id,
            messages=[{"role": "user", "content": "Say 'pong' and nothing else."}],
            max_tokens=10,
        )
        assert isinstance(result, ChatCompletionResponse)
        assert result.choices
        message = result.choices[0]["message"]
        # Fallback model may be a reasoner: any generated text proves the round trip.
        assert message.get("content") or message.get("reasoning_content"), message


async def test_chat_stream_text_deltas(api_key: str) -> None:
    # Real SSE framing through text_deltas: role opener, content deltas,
    # finish/usage chunks must all be filtered down to the text.
    async with AsyncVeniceClient(api_key=api_key) as client:
        models = await client.models.list(type="text")
        plain = [
            m
            for m in models.data
            if not (_spec(m).get("capabilities") or {}).get("supportsReasoning")
        ]
        if not plain:
            pytest.skip("No non-reasoning text model to stream from.")
        stream = await client.chat.stream(
            model=plain[0]["id"],
            messages=[{"role": "user", "content": "Count from 1 to 5, digits only."}],
            max_tokens=30,
        )
        texts = [t async for t in text_deltas(stream)]
        assert texts, "stream yielded no text"
        assert all(isinstance(t, str) and t for t in texts)
        assert "3" in "".join(texts)


async def test_image_styles(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.image.list_styles()
        assert isinstance(result, ImageStylesResponse)


# ---- billing usage history (free) ------------------------------------------


async def test_billing_usage_history_first_page(admin_key: str) -> None:
    async with AsyncVeniceClient(api_key=admin_key) as client:
        page = await client.billing.usage_history(page_size=10)
        assert isinstance(page, BillingUsageHistoryResponse)
        # Built via model_construct: assert the raw wire shape we depend on.
        assert isinstance(page.data, list)
        assert len(page.data) <= 10
        # ``nextCursor`` is required (null on the last page); model_construct
        # would silently leave it unset if Venice renamed or dropped it.
        assert "nextCursor" in page.model_fields_set
        assert page.nextCursor is None or isinstance(page.nextCursor, str)
        for entry in page.data:
            assert isinstance(entry, dict)
            assert {"timestamp", "sku", "amount", "currency"} <= entry.keys()


async def test_billing_usage_history_cursor_continuation(admin_key: str) -> None:
    """A continuation that sends *only* the cursor is accepted and pages forward."""
    async with AsyncVeniceClient(api_key=admin_key) as client:
        first = await client.billing.usage_history(page_size=10)
        cursor = getattr(first, "nextCursor", None)
        if not cursor:
            pytest.skip("Account has <= 10 usage entries - nothing to continue to.")
        second = await client.billing.usage_history(cursor=cursor)
        assert isinstance(second.data, list)
        # Ascending timestamp order across the page boundary.
        if first.data and second.data:
            assert first.data[-1]["timestamp"] <= second.data[0]["timestamp"]


async def test_billing_iter_usage_history_walks_two_pages(admin_key: str) -> None:
    async with AsyncVeniceClient(api_key=admin_key) as client:
        pages = []
        async for page in client.billing.iter_usage_history(page_size=10).iter_pages():
            pages.append(page)
            if len(pages) == 2:
                break
        assert pages and all(isinstance(p.data, list) for p in pages)


async def test_billing_usage_history_csv(admin_key: str) -> None:
    async with AsyncVeniceClient(api_key=admin_key) as client:
        page = await client.billing.usage_history_csv(page_size=10)
        assert isinstance(page, BillingUsageHistoryCsvPage)
        assert isinstance(page.content, bytes) and page.content
        assert page.next_cursor is None or isinstance(page.next_cursor, str)
        # Content-Disposition is documented for CSV; drift here is worth knowing.
        if page.filename is not None:
            assert page.filename.endswith(".csv")


# ---- retired endpoints still answer 410 (free) -------------------------------


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/billing/usage", None),
        ("POST", "/video/transcriptions", {"url": "https://example.com/v.mp4"}),
    ],
)
async def test_retired_endpoints_answer_410(
    api_key: str, method: str, path: str, body: dict[str, Any] | None
) -> None:
    """The deprecated SDK stubs short-circuit locally; this checks the premise.

    If Venice ever stops answering 410 here (endpoint revived, or a different
    status), the stubs and the VeniceGoneError mapping need revisiting.
    """
    async with AsyncVeniceClient(api_key=api_key) as client:
        with pytest.raises(VeniceGoneError) as info:
            await client._request_json(method, path, json_body=body)
        assert info.value.status_code == 410


# ---- decisions (beta; a few tokens) -------------------------------------------


async def test_models_list_decision_type(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.models.list(type="decision")
        assert isinstance(result, ModelList)


async def test_decisions_create_noul(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        models = await client.models.list(type="decision")
        if not models.data:
            pytest.skip("No decision models available on this account.")
        result = await client.decisions.create(
            model=models.data[0]["id"],
            state="The sky is blue on a clear day.",
            questions={"is_true": {"type": "noul", "instructions": "Is this statement true?"}},
        )
        assert isinstance(result, DecisionResponse)
        answer = result.answers["is_true"]
        assert answer["type"] == "noul"
        assert 0.0 <= answer["noul"] <= 1.0


# ---- voice changer --------------------------------------------------------------


async def test_voice_changer_quote(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        model = await _voice_changer_model(client)
        quote = await client.audio.voice_changer.quote(model=model["id"], duration_seconds=30)
        assert isinstance(quote, VoiceChangerQuoteResponse)
        assert isinstance(quote.quote, (int, float)) and quote.quote >= 0
        assert quote.duration_seconds == 30


async def test_voice_changer_round_trip(paid: str) -> None:
    """queue (multipart) → wait_for_completion (JSON then bytes) → complete.

    Billed: one TTS clip plus at least one minute of voice conversion.
    """
    async with AsyncVeniceClient(api_key=paid) as client:
        vc_model = await _voice_changer_model(client)
        formats = [str(f).lower() for f in _spec(vc_model).get("accepted_audio_formats") or []]
        if formats and "mp3" not in formats:
            pytest.skip(f"Voice-changer model accepts {formats}, not mp3 (TTS output).")

        tts_models = await client.models.list(type="tts")
        if not tts_models.data:
            pytest.skip("No TTS model available to produce a source clip.")
        tts_ids = [m["id"] for m in tts_models.data]
        tts_id = "tts-kokoro" if "tts-kokoro" in tts_ids else tts_ids[0]
        source = await client.audio.create_speech(
            input="Testing one two three.", model=tts_id, response_format="mp3"
        )
        assert source

        job = await client.audio.voice_changer.queue(model=vc_model["id"], file=source)
        assert job.queue_id
        assert job.duration_seconds is not None and job.duration_seconds > 0

        result = await client.audio.voice_changer.wait_for_completion(
            model=vc_model["id"],
            queue_id=job.queue_id,
            timeout_s=300,
            poll_interval_s=3,
        )
        assert result.status == "COMPLETED"
        assert result.audio, "completed retrieve should carry the converted audio bytes"
        assert result.content_type and not result.content_type.startswith("application/json")

        done = await client.audio.voice_changer.complete(
            model=vc_model["id"], queue_id=job.queue_id
        )
        assert done.success in (True, False)  # idempotent cleanup; either is valid


def _solid_png(size: int = 256, rgb: tuple[int, int, int] = (200, 40, 40)) -> bytes:
    """A valid solid-colour PNG built with zlib only (no Pillow dependency)."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    row = b"\x00" + bytes(rgb) * size
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(row * size))
        + chunk(b"IEND", b"")
    )


async def test_image_edit_header_metadata(paid: str, tmp_path: Path) -> None:
    """One /image/edit call with the default model: named fields reach the wire
    and the x-venice-* headers land on ImageBytes.metadata (GH #12 / #13).

    The swagger declares x-venice-is-blurred only on /image/generate; on edit it
    appears only in the safe_mode description, so this checks Venice really
    sends it. Billed: one image edit.
    """
    async with AsyncVeniceClient(api_key=paid) as client:
        result = await client.image.edit(
            image=_solid_png(),
            prompt="Add a small yellow star in the centre.",
            safe_mode=True,
            enhance_prompt=True,
            output_format="png",
        )
    assert isinstance(result, ImageBytes) and len(result) > 0
    meta = result.metadata
    print(f"edit metadata: {meta!r}")  # visible with -rA / on failure: records the live header set
    assert meta.content_type and meta.content_type.startswith("image/")
    assert meta.is_blurred is not None, f"no x-venice-is-blurred header; got {meta.headers}"
    saved = result.save(tmp_path / "edit.png")
    assert saved.read_bytes() == bytes(result)


def _flat_image_price(model: dict[str, Any]) -> float:
    """``pricing.generation.usd`` for flat-priced image models; inf otherwise."""
    pricing = _spec(model).get("pricing") or {}
    usd = (pricing.get("generation") or {}).get("usd") if isinstance(pricing, dict) else None
    return float(usd) if isinstance(usd, (int, float)) else float("inf")


async def test_image_generate_save_all(paid: str, tmp_path: Path) -> None:
    """Real base64 payloads from /image/generate decode and get a real image
    extension from their magic bytes (BACKLOG #24), for every requested format.

    Uses the cheapest flat-priced image model at a small size. Billed: one
    image per format (3).
    """
    async with AsyncVeniceClient(api_key=paid) as client:
        models = await client.models.list(type="image")
        priced = sorted(models.data, key=_flat_image_price)
        if not priced or _flat_image_price(priced[0]) == float("inf"):
            pytest.skip("No flat-priced image model listed on this account.")
        model = priced[0]["id"]
        for fmt, ext in (("png", "png"), ("jpeg", "jpg"), ("webp", "webp")):
            result = await client.image.generate(
                model=model,
                prompt="A plain red square.",
                width=512,
                height=512,
                format=fmt,
                safe_mode=True,
            )
            assert isinstance(result, GenerateImageResponse)
            paths = result.save_all(tmp_path / fmt, prefix="live")
            print(f"{model} {fmt}: {[p.name for p in paths]}")
            assert paths, "generate returned no images"
            for path in paths:
                # Magic-byte detection, not the request-format fallback: a
                # ".bin" or wrong suffix means Venice sent a format we don't sniff.
                assert path.suffix == f".{ext}", path
                assert path.stat().st_size > 100


async def test_audio_queue_direct_bytes_completion(paid: str) -> None:
    """queue → wait_for_completion on a model whose final poll returns the
    audio itself (``elevenlabs-tts-*``, per lewdresch's production logs).

    Checks BACKLOG #17: wait_for_completion returns COMPLETED with the bytes on
    ``.audio`` instead of failing on the non-JSON body. If Venice instead
    answers with a JSON COMPLETED status, the audio must come from
    retrieve_binary. Billed: one very short TTS job.
    """
    async with AsyncVeniceClient(api_key=paid) as client:
        models = await client.models.list(type="all")
        ids = sorted(
            m["id"] for m in models.data if str(m.get("id", "")).startswith("elevenlabs-tts")
        )
        if not ids:
            pytest.skip("No elevenlabs-tts-* model listed on this account.")
        model = ids[0]
        job = await client.audio.queue(model=model, prompt="Testing.")
        assert job.queue_id
        result = await client.audio.wait_for_completion(
            model=model, queue_id=job.queue_id, timeout_s=180, poll_interval_s=2
        )
        print(
            f"{model}: status={result.status} content_type={result.content_type} "
            f"audio_bytes={len(result.audio or b'')}"
        )
        assert result.status == "COMPLETED"
        if result.audio is None:  # JSON-status model after all: binary fetch must work
            audio = await client.audio.retrieve_binary(model=model, queue_id=job.queue_id)
            assert audio
        else:
            assert len(result.audio) > 100


async def test_record_rate_limit_headers(api_key: str) -> None:
    """Records which rate-limit headers Venice actually sends (BACKLOG #22).

    The spec documents none, so ``VeniceAPIError.rate_limit_headers`` captures
    any ``x-ratelimit-*`` / ``ratelimit-*`` raw. This free call prints what a
    normal response carries (visible in the CI log thanks to ``-rP``), so the
    names can be documented once seen. Asserts nothing about them.
    """
    async with AsyncVeniceClient(api_key=api_key) as client:
        response = await client._send("GET", "/models", json_body=None, params=None, headers=None)
    assert response.status_code == 200
    seen = {
        k: v
        for k, v in response.headers.items()
        if "ratelimit" in k.lower() or k.lower() in ("retry-after", "x-balance-remaining")
    }
    print(f"rate-limit-ish headers on GET /models: {seen}")
