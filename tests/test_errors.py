"""Tests for error parsing and status-code mapping."""

from __future__ import annotations

import pytest

from veniceresch import (
    VeniceAPIError,
    VeniceAuthError,
    VeniceContentViolationError,
    VeniceInsufficientBalanceError,
    VeniceNotFoundError,
    VeniceRateLimitError,
    VeniceServerError,
    VeniceValidationError,
    VeniceX402PaymentRequiredError,
)
from veniceresch._errors import raise_for_response


def test_2xx_response_is_noop(make_response):
    raise_for_response(make_response.json(200, {"ok": True}))
    raise_for_response(make_response.json(204, {}))


@pytest.mark.parametrize(
    ("status", "exc_cls"),
    [
        (400, VeniceValidationError),
        (401, VeniceAuthError),
        (402, VeniceInsufficientBalanceError),
        (404, VeniceNotFoundError),
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
    ]:
        assert issubclass(exc_cls, VeniceAPIError)
