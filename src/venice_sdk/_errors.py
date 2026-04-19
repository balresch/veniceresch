"""Exception hierarchy for Venice API calls.

The public types are:

* ``VeniceError`` — base class for anything raised by this SDK.
* ``VeniceAPIError`` — a non-2xx response came back from Venice.
* Subclasses per HTTP status family (auth, validation, rate-limit, ...).
* ``VeniceContentViolationError`` — Venice returned a ContentViolationError body,
  typically with a ``suggested_prompt``; detected by body shape, not status.

Mapping lives in :func:`raise_for_response`, which resource code uses to turn
a non-2xx :class:`httpx.Response` into the appropriate subclass.
"""

from __future__ import annotations

import json
from typing import Any

import httpx


class VeniceError(Exception):
    """Base class for every exception raised by venice-sdk."""


class VeniceAPIError(VeniceError):
    """A non-2xx response came back from Venice.

    Attributes:
        status_code: The HTTP status code from the response.
        error_body: Parsed JSON body if the server returned JSON, otherwise the
            raw response text.
        request: The :class:`httpx.Request` that was sent (useful for logging).
        response: The raw :class:`httpx.Response` (also useful for logging).
    """

    status_code: int
    error_body: dict[str, Any] | str

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error_body: dict[str, Any] | str,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_body = error_body
        self.request = request
        self.response = response


class VeniceAuthError(VeniceAPIError):
    """401 — API key is missing, malformed, or rejected."""


class VeniceInsufficientBalanceError(VeniceAPIError):
    """402 — Account balance (DIEM / VCU) is exhausted."""


class VeniceValidationError(VeniceAPIError):
    """400 or 422 — the request was malformed or failed schema validation."""


class VeniceNotFoundError(VeniceAPIError):
    """404 — the resource does not exist (e.g., unknown model or queue id)."""


class VeniceRateLimitError(VeniceAPIError):
    """429 — rate-limited. Retry with backoff (this SDK does not retry for you)."""


class VeniceServerError(VeniceAPIError):
    """5xx — Venice had an internal error."""


class VeniceContentViolationError(VeniceAPIError):
    """Response matched Venice's ContentViolationError schema.

    Venice returns this for prompts/outputs that trip its safety checks. The
    body usually includes a ``suggested_prompt`` that nudges the request back
    into policy. We detect by body shape (presence of ``suggested_prompt``)
    rather than status code, since Venice has used both 400 and 422 for this.
    """

    suggested_prompt: str | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error_body: dict[str, Any] | str,
        suggested_prompt: str | None = None,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            error_body=error_body,
            request=request,
            response=response,
        )
        self.suggested_prompt = suggested_prompt


def _parse_body(response: httpx.Response) -> dict[str, Any] | str:
    """Best-effort parse of a response body to JSON, else return the raw text."""
    try:
        parsed = response.json()
    except (json.JSONDecodeError, ValueError):
        return response.text
    if isinstance(parsed, dict):
        return parsed
    # Arrays or primitives — stringify so the type stays simple.
    return json.dumps(parsed)


def _message_from_body(body: dict[str, Any] | str, default: str) -> str:
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, str) and err:
            return err
        msg = body.get("message")
        if isinstance(msg, str) and msg:
            return msg
    elif body:
        return body[:500]
    return default


def raise_for_response(response: httpx.Response) -> None:
    """Raise the appropriate :class:`VeniceAPIError` subclass for a non-2xx response.

    2xx responses are a no-op. This function reads ``response.content`` and so
    must be called *after* the body is fully loaded (``response.read()`` for
    sync, ``await response.aread()`` for async).
    """
    if response.is_success:
        return

    body = _parse_body(response)
    status = response.status_code
    default_msg = f"Venice API returned HTTP {status}"
    message = _message_from_body(body, default_msg)
    kwargs: dict[str, Any] = {
        "status_code": status,
        "error_body": body,
        "request": response.request,
        "response": response,
    }

    # Content violations can come back as 400 or 422; detect by shape.
    if isinstance(body, dict) and "suggested_prompt" in body:
        suggested = body.get("suggested_prompt")
        raise VeniceContentViolationError(
            message,
            suggested_prompt=suggested if isinstance(suggested, str) else None,
            **kwargs,
        )

    exc_cls: type[VeniceAPIError]
    if status == 401:
        exc_cls = VeniceAuthError
    elif status == 402:
        exc_cls = VeniceInsufficientBalanceError
    elif status == 404:
        exc_cls = VeniceNotFoundError
    elif status in (400, 422):
        exc_cls = VeniceValidationError
    elif status == 429:
        exc_cls = VeniceRateLimitError
    elif 500 <= status < 600:
        exc_cls = VeniceServerError
    else:
        exc_cls = VeniceAPIError

    raise exc_cls(message, **kwargs)


__all__ = [
    "VeniceAPIError",
    "VeniceAuthError",
    "VeniceContentViolationError",
    "VeniceError",
    "VeniceInsufficientBalanceError",
    "VeniceNotFoundError",
    "VeniceRateLimitError",
    "VeniceServerError",
    "VeniceValidationError",
    "raise_for_response",
]
