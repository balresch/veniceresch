**Title:** Wrap httpx transport exceptions in typed `VeniceConnectionError` / `VeniceTimeoutError`

## Summary

Connection and timeout failures today bubble up as raw `httpx.ConnectError`, `httpx.ReadTimeout`, `httpx.WriteTimeout`, etc. The rest of the SDK raises typed subclasses of `VeniceError`, but these transport-level failures escape that hierarchy. Wrap them in SDK exception types so callers can write `except VeniceError` and catch everything.

## Motivation

The `_errors.py` module already provides a clean hierarchy for HTTP-level failures:

```
VeniceError
├── VeniceAPIError
│   ├── VeniceAuthError (401)
│   ├── VeniceInsufficientBalanceError (402)
│   ├── VeniceValidationError (400/422)
│   ├── VeniceNotFoundError (404)
│   ├── VeniceRateLimitError (429)
│   ├── VeniceServerError (5xx)
│   └── VeniceContentViolationError (body-shape)
└── (everything else escapes as raw httpx.*)
```

Callers who want to handle any retriable failure currently need:

```python
try:
    await client.chat.create(...)
except (VeniceRateLimitError, VeniceServerError, httpx.ConnectError, httpx.ReadTimeout,
        httpx.WriteTimeout, httpx.PoolTimeout):
    retry()
```

The `httpx.*` imports are an abstraction leak — users shouldn't have to know the SDK's transport is httpx (it could be aiohttp or urllib3 in a future major version, and their `except` clauses would silently stop catching things).

Concrete evidence: the lewdresch codebase's `src/lewdresch/venice/retry.py` currently imports `APIConnectionError, APITimeoutError` from the abandoned community SDK specifically for this reason. Every migrating user will end up inventing the same wrappers.

## Proposed solution

### 1. Define two new exception types

```python
# src/venice_sdk/_errors.py

class VeniceConnectionError(VeniceError):
    """Network-level failure reaching Venice (DNS, TLS, connection reset, proxy)."""

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class VeniceTimeoutError(VeniceError):
    """Request or response timed out before completion."""

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause
```

Both inherit from `VeniceError` but not `VeniceAPIError` — they're transport failures, not API responses.

### 2. Wrap httpx exceptions in the transport layer

```python
# src/venice_sdk/_client.py
import httpx

async def _send(self, method: str, path: str, **kwargs) -> httpx.Response:
    url = self._url_for(path)
    ...
    try:
        response = await self._http.request(method, url, ...)
    except httpx.TimeoutException as exc:
        raise VeniceTimeoutError(
            f"Request to {method} {path} timed out after {self._timeout}s"
        ) from exc
    except httpx.ConnectError as exc:
        raise VeniceConnectionError(
            f"Could not connect to {url}: {exc}"
        ) from exc
    except httpx.HTTPError as exc:
        # Catch-all for less common httpx errors (NetworkError, ProtocolError, etc.)
        raise VeniceConnectionError(
            f"HTTP transport error on {method} {path}: {exc}"
        ) from exc

    if not response.is_success:
        raise_for_response(response)
    return response
```

Repeat for:
- The sync `_send`.
- The async and sync streaming context managers (`_request_stream`) — they call `self._http.stream` and need the same try/except.

### 3. Re-export the new types

```python
# src/venice_sdk/__init__.py
from venice_sdk._errors import (
    ...
    VeniceConnectionError,
    VeniceTimeoutError,
)
```

### 4. Update docs

README's error-handling table:

| Exception | When |
|---|---|
| `VeniceAuthError` | 401 — bad or missing API key |
| `VeniceInsufficientBalanceError` | 402 — balance exhausted |
| `VeniceValidationError` | 400 / 422 — bad request shape |
| `VeniceNotFoundError` | 404 |
| `VeniceRateLimitError` | 429 |
| `VeniceServerError` | 5xx |
| `VeniceContentViolationError` | body contained `suggested_prompt` |
| **`VeniceConnectionError`** | **DNS / TLS / connection reset / proxy failure** |
| **`VeniceTimeoutError`** | **Request or response timed out** |

Common retry snippet becomes:

```python
from venice_sdk import (
    VeniceConnectionError, VeniceRateLimitError, VeniceServerError, VeniceTimeoutError,
)

try:
    await client.chat.create(...)
except (VeniceRateLimitError, VeniceServerError, VeniceConnectionError, VeniceTimeoutError):
    retry()
```

No `httpx.*` imports at the call site.

## Preserving the original exception

Both wrappers set `__cause__` (via `raise ... from exc`) so debugging still points at the underlying httpx class when needed. `VeniceConnectionError.__cause__` is still an `httpx.ConnectError` for users who want to introspect.

## Acceptance criteria

- [ ] `VeniceConnectionError` and `VeniceTimeoutError` exist in `_errors.py` and are re-exported from `venice_sdk`.
- [ ] Both inherit from `VeniceError` (not `VeniceAPIError`).
- [ ] Transport-level failures in both sync and async `_send` and `_request_stream` raise the wrapper, not raw `httpx.*`.
- [ ] `__cause__` chain preserves the original httpx exception.
- [ ] Tests:
  ```python
  async def test_connect_error_wraps_to_venice_connection_error():
      async_client = AsyncVeniceClient(api_key="k", http_client=httpx.AsyncClient(transport=_raising_transport(httpx.ConnectError("dns failed"))))
      with pytest.raises(VeniceConnectionError) as exc:
          await async_client.chat.create(model="m", messages=[...])
      assert isinstance(exc.value.__cause__, httpx.ConnectError)

  async def test_read_timeout_wraps_to_venice_timeout_error():
      # similar, with httpx.ReadTimeout
  ```
- [ ] README's error table documents the two new types.

## Backwards compatibility

This is semi-breaking: anyone today with `except httpx.ConnectError` will stop catching transport failures. The change is in the right direction (wrapping external library exceptions behind the SDK's hierarchy) and pre-1.0 is the right time to make it. Document in `CHANGELOG.md` and bump minor version.

## Estimated scope

~2 hours including tests on both sync and async paths.
