"""Tests for error parsing and status-code mapping."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

import veniceresch
from veniceresch import (
    VeniceAPIError,
    VeniceAuthError,
    VeniceConflictError,
    VeniceContentViolationError,
    VeniceGoneError,
    VeniceInsufficientBalanceError,
    VeniceNotFoundError,
    VenicePayloadTooLargeError,
    VenicePermissionError,
    VeniceProviderContentPolicyError,
    VeniceRateLimitError,
    VeniceServerError,
    VeniceValidationError,
    VeniceX402PaymentRequiredError,
)
from veniceresch._errors import _parse_retry_after, raise_for_response
from veniceresch.resources._polling import VeniceJobFailedError


def test_2xx_response_is_noop(make_response):
    raise_for_response(make_response.json(200, {"ok": True}))
    raise_for_response(make_response.json(204, {}))


@pytest.mark.parametrize(
    ("status", "exc_cls"),
    [
        (400, VeniceValidationError),
        (401, VeniceAuthError),
        (402, VeniceInsufficientBalanceError),
        (403, VenicePermissionError),
        (404, VeniceNotFoundError),
        (409, VeniceConflictError),
        (410, VeniceGoneError),
        (413, VenicePayloadTooLargeError),
        (422, VeniceValidationError),
        (429, VeniceRateLimitError),
        (500, VeniceServerError),
        (503, VeniceServerError),
        (418, VeniceAPIError),  # unmapped → base class
    ],
)
def test_status_maps_to_exception(status, exc_cls, make_response):
    response = make_response.json(status, {"error": "something went wrong"})
    with pytest.raises(exc_cls) as info:
        raise_for_response(response)
    assert info.value.status_code == status
    assert str(info.value) == "something went wrong"
    assert info.value.error_body == {"error": "something went wrong"}


def test_content_violation_detected_by_body_shape(make_response):
    # Server sends 400 with a suggested_prompt — that's a content violation,
    # not a generic validation error.
    body = {
        "error": "Your prompt hit the safety filter",
        "suggested_prompt": "a tamer version",
    }
    response = make_response.json(400, body)
    with pytest.raises(VeniceContentViolationError) as info:
        raise_for_response(response)
    assert info.value.suggested_prompt == "a tamer version"
    assert info.value.status_code == 400


def test_content_violation_precedence_over_status(make_response):
    # Even with a 422 that would normally map to VeniceValidationError,
    # the body shape wins.
    body = {"error": "policy", "suggested_prompt": "try again"}
    response = make_response.json(422, body)
    with pytest.raises(VeniceContentViolationError):
        raise_for_response(response)


def test_provider_content_policy_detected_by_body_shape(make_response):
    # A 422 whose nested error.type is provider_content_policy is a provider
    # rejection (credits refunded), distinct from VeniceContentViolationError.
    body = {
        "error": {
            "message": "Provider rejected this request. Try wan-2-7-text-to-video.",
            "type": "provider_content_policy",
            "recommended_model": "wan-2-7-text-to-video",
            "credits_refunded": True,
        }
    }
    response = make_response.json(422, body)
    with pytest.raises(VeniceProviderContentPolicyError) as info:
        raise_for_response(response)
    assert info.value.status_code == 422
    assert info.value.recommended_model == "wan-2-7-text-to-video"
    assert info.value.credits_refunded is True
    assert "Provider rejected" in str(info.value)


def test_payload_too_large_body_preserved(make_response):
    body = {"code": "PAYLOAD_TOO_LARGE", "error": "File exceeds 25 MB."}
    response = make_response.json(413, body)
    with pytest.raises(VenicePayloadTooLargeError) as info:
        raise_for_response(response)
    assert info.value.status_code == 413
    assert str(info.value) == "File exceeds 25 MB."


def test_x402_payment_required_detected_by_body_shape(make_response):
    # A 402 whose body carries x402Version + accepts is the x402 discovery
    # payload, not a DIEM-balance-exhausted error.
    body = {
        "x402Version": 2,
        "accepts": [
            {
                "protocol": "x402",
                "version": 2,
                "network": "eip155:8453",
                "asset": "0xUSDC",
                "amount": "5000000",
                "payTo": "0xreceiver",
            }
        ],
    }
    response = make_response.json(402, body)
    with pytest.raises(VeniceX402PaymentRequiredError) as info:
        raise_for_response(response)
    assert info.value.status_code == 402
    assert info.value.x402_version == 2
    assert info.value.accepts[0]["asset"] == "0xUSDC"


def test_plain_402_still_raises_insufficient_balance(make_response):
    # Without x402Version + accepts, a 402 is a regular
    # VeniceInsufficientBalanceError (Venice DIEM/USD exhausted).
    response = make_response.json(402, {"error": "balance exhausted"})
    with pytest.raises(VeniceInsufficientBalanceError):
        raise_for_response(response)


def test_non_json_body_still_raises(make_response):
    response = make_response.text(500, "<html>nginx gateway timeout</html>")
    with pytest.raises(VeniceServerError) as info:
        raise_for_response(response)
    assert info.value.status_code == 500
    # Body preserved as raw text when not JSON.
    assert isinstance(info.value.error_body, str)
    assert "nginx" in info.value.error_body


def test_message_falls_back_to_default_when_body_empty(make_response):
    response = make_response.json(500, {})
    with pytest.raises(VeniceServerError) as info:
        raise_for_response(response)
    assert "HTTP 500" in str(info.value)


def test_exception_hierarchy():
    # All specific errors are VeniceAPIError, which is VeniceError.
    for exc_cls in [
        VeniceAuthError,
        VeniceValidationError,
        VeniceNotFoundError,
        VeniceRateLimitError,
        VeniceServerError,
        VeniceInsufficientBalanceError,
        VeniceContentViolationError,
        VeniceX402PaymentRequiredError,
        VenicePermissionError,
        VeniceConflictError,
        VeniceGoneError,
    ]:
        assert issubclass(exc_cls, VeniceAPIError)


def test_ip_restricted_403_maps_to_permission_error(make_response):
    msg = (
        "This API key is restricted to configured IP addresses, and this "
        "request's source IP is not allowed"
    )
    with pytest.raises(VenicePermissionError) as info:
        raise_for_response(make_response.json(403, {"error": msg}))
    assert str(info.value) == msg


def test_gone_410_surfaces_sunset_headers():
    request = httpx.Request("GET", "https://api.venice.ai/api/v1/billing/usage")
    response = httpx.Response(
        410,
        json={"error": "Use GET /api/v1/billing/usage-history"},
        headers={
            "Sunset": "Wed, 16 Sep 2026 00:00:00 GMT",
            "Deprecation": "@1780000000",
            "Link": '</api/v1/billing/usage-history>; rel="successor-version"',
        },
        request=request,
    )
    with pytest.raises(VeniceGoneError) as info:
        raise_for_response(response)
    exc = info.value
    assert exc.status_code == 410
    assert exc.sunset == "Wed, 16 Sep 2026 00:00:00 GMT"
    assert exc.deprecation == "@1780000000"
    assert "usage-history" in (exc.link or "")


def test_gone_410_without_headers_leaves_attrs_none(make_response):
    with pytest.raises(VeniceGoneError) as info:
        raise_for_response(make_response.json(410, {"error": "gone"}))
    assert (info.value.sunset, info.value.deprecation, info.value.link) == (None, None, None)


def test_image_content_violation_exposes_recommended_model_and_retryable(make_response):
    body = {
        "error": "Rejected by provider moderation",
        "suggested_prompt": "a calmer scene",
        "recommended_model": "flux-2-max",
        "retryable": True,
    }
    with pytest.raises(VeniceContentViolationError) as info:
        raise_for_response(make_response.json(422, body))
    exc = info.value
    assert exc.suggested_prompt == "a calmer scene"
    assert exc.recommended_model == "flux-2-max"
    assert exc.retryable is True


def test_content_violation_new_fields_default_to_none(make_response):
    with pytest.raises(VeniceContentViolationError) as info:
        raise_for_response(make_response.json(400, {"error": "x", "suggested_prompt": "y"}))
    assert info.value.recommended_model is None
    assert info.value.retryable is None


# ---- caller-owned retry helpers (BACKLOG #22) -----------------------------


_NOW = datetime(2026, 11, 16, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("120", 120.0),
        ("0", 0.0),
        (" 1.5 ", 1.5),
        ("Mon, 16 Nov 2026 12:00:30 GMT", 30.0),  # HTTP date, 30s from _NOW
        ("Mon, 16 Nov 2026 11:59:00 GMT", 0.0),  # already past -> 0
        ("-5", None),
        ("nan", None),
        ("soon", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_retry_after(value, expected):
    assert _parse_retry_after(value, now=_NOW) == expected


async def test_rate_limit_error_carries_retry_after_and_headers(mock_api, async_client):
    mock_api.get("/models").respond(
        429,
        json={"error": "slow down"},
        headers={
            "Retry-After": "7",
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-reset-requests": "7s",
            "RateLimit-Policy": "100;w=60",
            "x-unrelated": "no",
        },
    )
    with pytest.raises(veniceresch.VeniceRateLimitError) as info:
        await async_client.models.list()
    exc = info.value
    assert exc.retry_after == 7.0
    assert exc.rate_limit_headers == {
        "x-ratelimit-remaining-requests": "0",
        "x-ratelimit-reset-requests": "7s",
        "ratelimit-policy": "100;w=60",
    }
    assert veniceresch.is_retryable(exc)


def test_server_error_retry_after_and_absent_headers(mock_api, sync_client):
    mock_api.get("/models").respond(503, text="busy", headers={"Retry-After": "2"})
    with pytest.raises(veniceresch.VeniceServerError) as info:
        sync_client.models.list()
    assert info.value.retry_after == 2.0
    assert info.value.rate_limit_headers == {}


def test_error_without_response_has_empty_retry_fields():
    exc = veniceresch.VeniceAPIError("x", status_code=500, error_body={})
    assert exc.retry_after is None and exc.rate_limit_headers == {}


def _api(cls, status, **kw):
    return cls("x", status_code=status, error_body={}, **kw)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (veniceresch.VeniceConnectionError("reset"), True),
        (veniceresch.VeniceTimeoutError("read timed out"), True),
        (_api(veniceresch.VeniceRateLimitError, 429), True),
        (_api(veniceresch.VeniceServerError, 500), True),
        (_api(veniceresch.VeniceServerError, 503), True),
        (_api(veniceresch.VeniceAPIError, 408), True),
        (_api(veniceresch.VeniceAPIError, 418), False),
        (_api(veniceresch.VeniceAuthError, 401), False),
        (_api(veniceresch.VeniceInsufficientBalanceError, 402), False),
        (_api(veniceresch.VenicePermissionError, 403), False),
        (_api(veniceresch.VeniceNotFoundError, 404), False),
        (_api(veniceresch.VeniceConflictError, 409), False),
        (_api(veniceresch.VeniceValidationError, 400), False),
        (_api(veniceresch.VenicePayloadTooLargeError, 413), False),
        (_api(veniceresch.VeniceContentViolationError, 400, retryable=True), True),
        (_api(veniceresch.VeniceContentViolationError, 400, retryable=False), False),
        (_api(veniceresch.VeniceContentViolationError, 400), False),
        (_api(veniceresch.VeniceUnexpectedContentTypeError, 200), False),
        (veniceresch.VeniceVideoTimeoutError("q1", 60.0), False),
        (veniceresch.VeniceAudioTimeoutError("q1", 60.0), False),
        (VeniceJobFailedError("q1", "FAILED", {}, kind="video"), False),
        (ValueError("not ours"), False),
        (httpx.ConnectError("raw httpx, never raised by the SDK"), False),
    ],
    ids=lambda v: type(v).__name__ if isinstance(v, BaseException) else str(v),
)
def test_is_retryable(exc, expected):
    assert veniceresch.is_retryable(exc) is expected
