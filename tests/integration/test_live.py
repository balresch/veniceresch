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
* **Paid** (opt-in with ``VENICE_INTEGRATION_PAID=1``): flows that are billed
  per job — e.g. the voice-changer round trip, which Venice charges by the
  minute (rounded up), plus the TTS call that produces its source clip. The
  weekly scheduled CI run leaves this off; trigger it manually with the
  workflow's ``paid`` input.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from veniceresch import AsyncVeniceClient, VeniceGoneError
from veniceresch.types import (
    BillingBalanceResponse,
    BillingUsageHistoryCsvPage,
    BillingUsageHistoryResponse,
    ChatCompletionResponse,
    DecisionResponse,
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


async def test_billing_balance(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.billing.balance()
        assert isinstance(result, BillingBalanceResponse)


async def test_chat_completion_minimal(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        models = await client.models.list(type="text")
        if not models.data:
            pytest.skip("No text models available on this account.")
        model_id = models.data[0]["id"]
        result = await client.chat.create(
            model=model_id,
            messages=[{"role": "user", "content": "Say 'pong' and nothing else."}],
            max_tokens=10,
        )
        assert isinstance(result, ChatCompletionResponse)
        assert result.choices and result.choices[0]["message"]["content"]


async def test_image_styles(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        result = await client.image.list_styles()
        assert isinstance(result, ImageStylesResponse)


# ---- billing usage history (free) ------------------------------------------


async def test_billing_usage_history_first_page(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
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


async def test_billing_usage_history_cursor_continuation(api_key: str) -> None:
    """A continuation that sends *only* the cursor is accepted and pages forward."""
    async with AsyncVeniceClient(api_key=api_key) as client:
        first = await client.billing.usage_history(page_size=10)
        cursor = getattr(first, "nextCursor", None)
        if not cursor:
            pytest.skip("Account has <= 10 usage entries - nothing to continue to.")
        second = await client.billing.usage_history(cursor=cursor)
        assert isinstance(second.data, list)
        # Ascending timestamp order across the page boundary.
        if first.data and second.data:
            assert first.data[-1]["timestamp"] <= second.data[0]["timestamp"]


async def test_billing_iter_usage_history_walks_two_pages(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
        pages = []
        async for page in client.billing.iter_usage_history(page_size=10).iter_pages():
            pages.append(page)
            if len(pages) == 2:
                break
        assert pages and all(isinstance(p.data, list) for p in pages)


async def test_billing_usage_history_csv(api_key: str) -> None:
    async with AsyncVeniceClient(api_key=api_key) as client:
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
