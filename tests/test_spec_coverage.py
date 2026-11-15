"""Every operation in the vendored Venice spec is wired to a client method (BACKLOG #21).

``OPERATIONS`` maps each ``(METHOD, path)`` in ``vendor/venice-swagger.yaml`` to
the resource method that calls it, with minimal arguments. Each entry is
*executed* against respx on both the async and the sync client, and the test
asserts the request really went to that method + path. So this checks the
wiring, not just that a method exists.

``EXCLUDED`` lists operations deliberately not wrapped, with the reason.
``RETIRED`` lists operations Venice answers with 410, whose deprecated stubs
must raise :class:`VeniceGoneError` locally without a request.

When a spec regen adds, removes or renames an operation, the set test fails:
wrap the new operation (and add it here), or add it to ``EXCLUDED`` with a
reason. That keeps the "covers every documented path" claim honest.
"""

from __future__ import annotations

import inspect
import re
import warnings
from pathlib import Path
from typing import Any

import pytest
import yaml

from veniceresch import VeniceGoneError
from veniceresch._client import DEFAULT_BASE_URL

SPEC_PATH = Path(__file__).resolve().parent.parent / "vendor" / "venice-swagger.yaml"
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
BASE_PATH = re.sub(r"^https?://[^/]+", "", DEFAULT_BASE_URL)  # "/api/v1"

_MSGS = [{"role": "user", "content": "hi"}]
_FILE = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 16

# (METHOD, spec path) -> (dotted resource method, kwargs, path params for the template)
OPERATIONS: dict[tuple[str, str], tuple[str, dict[str, Any], dict[str, str]]] = {
    ("POST", "/chat/completions"): ("chat.create", {"model": "m", "messages": _MSGS}, {}),
    ("POST", "/responses"): ("responses.create", {"model": "m", "input": "hi"}, {}),
    ("POST", "/image/generate"): ("image.generate", {"model": "m", "prompt": "p"}, {}),
    ("POST", "/images/generations"): ("images.generate", {"prompt": "p"}, {}),
    ("GET", "/image/styles"): ("image.list_styles", {}, {}),
    ("POST", "/image/upscale"): ("image.upscale", {"image": "https://x/i.png"}, {}),
    ("POST", "/image/edit"): ("image.edit", {"image": "https://x/i.png", "prompt": "p"}, {}),
    ("POST", "/image/multi-edit"): (
        "image.multi_edit",
        {"images": ["https://x/i.png"], "prompt": "p"},
        {},
    ),
    ("POST", "/image/background-remove"): (
        "image.background_remove",
        {"image_url": "https://x/i.png"},
        {},
    ),
    ("GET", "/models"): ("models.list", {}, {}),
    ("GET", "/models/traits"): ("models.list_traits", {}, {}),
    ("GET", "/models/compatibility_mapping"): ("models.compatibility_mapping", {}, {}),
    ("GET", "/api_keys"): ("api_keys.list", {}, {}),
    ("DELETE", "/api_keys"): ("api_keys.delete", {"id": "k1"}, {}),
    ("POST", "/api_keys"): (
        "api_keys.create",
        {"api_key_type": "INFERENCE", "description": "d"},
        {},
    ),
    ("PATCH", "/api_keys"): ("api_keys.update", {"id": "k1"}, {}),
    ("GET", "/api_keys/{id}"): ("api_keys.get", {"id": "k1"}, {"id": "k1"}),
    ("GET", "/api_keys/rate_limits"): ("api_keys.rate_limits", {}, {}),
    ("GET", "/api_keys/rate_limits/log"): ("api_keys.rate_limits_log", {}, {}),
    ("GET", "/api_keys/generate_web3_key"): ("api_keys.generate_web3_key_challenge", {}, {}),
    ("POST", "/api_keys/generate_web3_key"): (
        "api_keys.generate_web3_key",
        {"api_key_type": "INFERENCE", "address": "0x1", "signature": "s", "token": "t"},
        {},
    ),
    ("GET", "/characters"): ("characters.list", {}, {}),
    ("GET", "/characters/{slug}"): ("characters.get", {"slug": "c1"}, {"slug": "c1"}),
    ("GET", "/characters/{slug}/reviews"): (
        "characters.reviews",
        {"slug": "c1"},
        {"slug": "c1"},
    ),
    ("POST", "/embeddings"): ("embeddings.create", {"input": "hi", "model": "m"}, {}),
    ("POST", "/decisions"): (
        "decisions.create",
        {"model": "m", "state": "s", "questions": {"q": {"type": "noul", "question": "?"}}},
        {},
    ),
    ("POST", "/audio/speech"): ("audio.create_speech", {"input": "hi"}, {}),
    ("POST", "/audio/transcriptions"): ("audio.transcribe", {"file": _FILE}, {}),
    ("POST", "/audio/voices"): ("audio.create_cloned_voice", {"file": _FILE}, {}),
    ("POST", "/video/complete"): ("video.complete", {"queue_id": "q"}, {}),
    ("POST", "/video/queue"): ("video.queue", {"model": "m"}, {}),
    ("POST", "/video/quote"): ("video.quote", {"model": "m"}, {}),
    ("POST", "/video/retrieve"): ("video.retrieve", {"queue_id": "q"}, {}),
    ("POST", "/augment/text-parser"): ("augment.parse", {"file": b"hello"}, {}),
    ("POST", "/audio/complete"): ("audio.complete", {"model": "m", "queue_id": "q"}, {}),
    ("POST", "/audio/queue"): ("audio.queue", {"model": "m", "prompt": "p"}, {}),
    ("POST", "/audio/quote"): ("audio.quote", {"model": "m"}, {}),
    ("POST", "/audio/retrieve"): ("audio.retrieve", {"model": "m", "queue_id": "q"}, {}),
    ("POST", "/audio/voice-changer/queue"): (
        "audio.voice_changer.queue",
        {"model": "m", "audio_url": "https://x/a.mp3"},
        {},
    ),
    ("POST", "/audio/voice-changer/quote"): (
        "audio.voice_changer.quote",
        {"model": "m", "duration_seconds": 30},
        {},
    ),
    ("POST", "/audio/voice-changer/retrieve"): (
        "audio.voice_changer.retrieve",
        {"model": "m", "queue_id": "q"},
        {},
    ),
    ("POST", "/audio/voice-changer/complete"): (
        "audio.voice_changer.complete",
        {"model": "m", "queue_id": "q"},
        {},
    ),
    ("GET", "/billing/balance"): ("billing.balance", {}, {}),
    ("GET", "/billing/usage-analytics"): ("billing.usage_analytics", {}, {}),
    ("GET", "/billing/usage-history"): ("billing.usage_history", {}, {}),
    ("GET", "/crypto/rpc/networks"): ("crypto.networks", {}, {}),
    ("POST", "/crypto/rpc/{network}"): (
        "crypto.rpc",
        {"network": "base", "request": {"jsonrpc": "2.0", "method": "eth_chainId", "id": 1}},
        {"network": "base"},
    ),
    ("GET", "/x402/balance/{walletAddress}"): (
        "x402.balance",
        {"wallet_address": "0xabc", "siwx_header": "h"},
        {"walletAddress": "0xabc"},
    ),
    ("POST", "/x402/top-up"): ("x402.top_up", {}, {}),
    ("GET", "/x402/transactions/{walletAddress}"): (
        "x402.transactions",
        {"wallet_address": "0xabc", "siwx_header": "h"},
        {"walletAddress": "0xabc"},
    ),
    ("POST", "/augment/scrape"): ("augment.scrape", {"url": "https://x"}, {}),
    ("POST", "/augment/search"): ("augment.search", {"query": "q"}, {}),
}

EXCLUDED: dict[tuple[str, str], str] = {
    ("POST", "/systemone"): "upstream alias of /decisions; use decisions.create",
}

# Retired upstream (410). Deprecated stubs raise VeniceGoneError locally; removed in 1.0.
RETIRED: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {
    ("GET", "/billing/usage"): ("billing.usage", {}),
    ("POST", "/video/transcriptions"): ("video.transcribe", {"url": "https://x/v.mp4"}),
}


def _spec_operations() -> set[tuple[str, str]]:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    return {
        (method.upper(), path)
        for path, ops in spec["paths"].items()
        for method in ops
        if method in HTTP_METHODS
    }


def _resolve(client: Any, dotted: str) -> Any:
    obj = client
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


def test_every_spec_operation_is_mapped_excluded_or_retired():
    spec_ops = _spec_operations()
    known = set(OPERATIONS) | set(EXCLUDED) | set(RETIRED)
    missing = sorted(spec_ops - known)
    stale = sorted(known - spec_ops)
    assert not missing, (
        f"Spec operations not wired to a client method: {missing}. Wrap them and add "
        "them to OPERATIONS, or add them to EXCLUDED with a reason."
    )
    assert not stale, f"Mapped operations no longer in the spec: {stale}. Remove or update them."
    overlap = (set(OPERATIONS) & set(EXCLUDED)) | (set(OPERATIONS) & set(RETIRED))
    assert not overlap


@pytest.mark.parametrize("flavor", ["async", "sync"])
@pytest.mark.parametrize("op", sorted(OPERATIONS), ids=lambda op: f"{op[0]} {op[1]}")
async def test_operation_hits_its_spec_path(mock_api, async_client, sync_client, flavor, op):
    method, template = op
    dotted, kwargs, path_params = OPERATIONS[op]
    expected_path = BASE_PATH + template.format(**path_params)
    route = mock_api.route().respond(200, json={})

    func = _resolve(async_client if flavor == "async" else sync_client, dotted)
    try:
        result = func(**kwargs)
        if inspect.isawaitable(result):
            await result
    except Exception as exc:  # response-shape errors after the send don't matter here
        if not route.called:
            raise AssertionError(f"{dotted} raised before sending a request: {exc!r}") from exc

    assert route.call_count == 1, f"{dotted} sent {route.call_count} requests"
    request = route.calls.last.request
    assert (request.method, request.url.path) == (method, expected_path)


@pytest.mark.parametrize("op", sorted(RETIRED), ids=lambda op: f"{op[0]} {op[1]}")
async def test_retired_operation_raises_gone_locally(mock_api, async_client, op):
    dotted, kwargs = RETIRED[op]
    route = mock_api.route().respond(200, json={})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        with pytest.raises(VeniceGoneError):
            result = _resolve(async_client, dotted)(**kwargs)
            if inspect.isawaitable(result):
                await result
    assert not route.called
