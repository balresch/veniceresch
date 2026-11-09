# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A typed, async-first Python client for the Venice.ai API. Venice publishes no official Python SDK but does maintain an OpenAPI 3.0 spec at `github.com/veniceai/api-docs/blob/main/swagger.yaml` — that spec is the source of truth for types.

`CHANGELOG.md` tracks what shipped per release.

## Architecture — the split that matters

Two distinct layers; they must stay distinct:

1. **`src/veniceresch/_generated.py`** — auto-generated from `vendor/venice-swagger.yaml` by `datamodel-code-generator`. **Never hand-edit.** Regenerate via `bash scripts/regen_types.sh [--offline]`. Committed so installs don't need the generator. mypy/ruff ignore it.
2. **Hand-written thin layer**:
   - `_client.py` — `AsyncVeniceClient` + `VeniceClient` (httpx wrapper). Both own their httpx session by default; callers can inject one for reuse. Internal helpers: `_request_json` (JSON in/out), `_request_any` (arrays), `_request_bytes` (binary responses), `_request_stream` (SSE / streaming). `_request_json` / `_send` take `no_auth=True` to strip the default `Authorization: Bearer …` for endpoints that use another auth scheme (x402 SIWE, `/api_keys/generate_web3_key`).
   - `_errors.py` — typed exception hierarchy. `raise_for_response()` maps non-2xx responses. Content-violation detection by body shape (`suggested_prompt`), not status, because Venice has used both 400 and 422 for them; the image-flavored body's `recommended_model` / `retryable` are surfaced too. Status classes: 401 auth, 402 balance, 403 `VenicePermissionError` (e.g. key `ipAllowlist`), 404, 409 `VeniceConflictError`, 410 `VeniceGoneError`, 400/422 validation, 413, 429, 5xx. A 402 whose body carries `x402Version` + `accepts` is surfaced as `VeniceX402PaymentRequiredError` (not `VeniceInsufficientBalanceError`) — that body is the x402 discovery payload, not an error. `translate_httpx_error()` wraps transport-level httpx errors as `VeniceConnectionError` / `VeniceTimeoutError`.
   - `_base_model.py` — `VeniceBaseModel` with `ConfigDict(extra="allow")`; the shared base for every Pydantic model (both generated and hand-written). Unknown fields land on `.model_extra` instead of raising.
   - `types.py` — re-exports generated response models plus hand-authored ones for endpoints whose swagger response is inline (no named schema).
   - `pagination.py` — `AsyncPaginator` / `Paginator` generic classes. Endpoint-agnostic: each `iter_*` resource method passes three closures (fetch / extract items / compute next params or None). Lazy — no HTTP until `async for` / `for` starts. `__aiter__` / `__iter__` yield items; `.iter_pages()` yields pages.
   - `resources/*.py` — one module per endpoint group. Each method maps swagger `requestBody.properties` to kwargs, calls the client helper, returns a typed Pydantic model or raw `bytes`. Resources don't construct httpx requests directly.

`client.chat`, `client.responses`, `client.image`, `client.images` (OpenAI alias), `client.video`, `client.audio`, `client.models`, `client.embeddings`, `client.billing`, `client.augment`, `client.characters`, `client.api_keys`, `client.x402`, `client.crypto`, `client.decisions` are wired in both client constructors. `client.chat.completions` is an OpenAI-namespace alias for `client.chat`; `client.audio.voice_changer` is a sub-resource for `/audio/voice-changer/*`.

## Non-goals

- **No retry/backoff logic.** The SDK only raises typed exceptions so callers can dispatch and plug in their own retry policy.
- **No CLI.** Library only.
- **No SSE parsers beyond plain dict events.** `resources/_sse.py` stops at `[DONE]` and yields decoded JSON (wrapped into `ChatCompletionChunk` at the chat resource layer).

## Venice-specific ergonomics

- **`venice_parameters`** — Venice extends chat completions with an extras object. First-class kwarg in `chat.create` / `chat.stream`.
- **Binary responses** — image edit/multi-edit/upscale/background-remove return raw PNG bytes. Resource methods return `bytes`. For image-generate, `generate()` returns a `GenerateImageResponse` (JSON) and `generate_binary()` returns bytes (forces `return_binary=True`).
- **Video polling** — `/video/queue` gives a `queue_id`; caller polls `/video/retrieve` until `status != "PROCESSING"`. The `wait_for_completion(queue_id, model, timeout_s, poll_interval_s)` helper is the only resource method with real logic beyond "post and parse." Raises `VeniceVideoTimeoutError` on deadline. Audio has the same pattern. Queue/retrieve/quote/complete methods return hand-authored Pydantic wrappers (`VideoQueueResponse`, `AudioRetrieveResponse`, …), not `dict`.
- **`model_id` vs `model`** — `/image/multi-edit` uses `modelId` (camelCase) in the spec; the Python API accepts `model_id` and translates. Everywhere else it's `model`.
- **`_send` for header-bearing responses** — when a resource needs response *headers* or must branch on content type (`billing.usage_history_csv` reads `x-next-cursor`; `voice_changer.retrieve`), it calls `client._send(...)` directly and gets the `httpx.Response` back (still error-mapped). Everything else stays on the `_request_*` helpers.
- **Binary Accept header** — `_request_bytes` sets `Accept: application/octet-stream` by default, but caller-provided `headers={"Accept": ...}` wins. Needed for `video/mp4`, `audio/mpeg`, etc.
- **Streaming await contract** — `await client.chat.stream(...)` or `await client.chat.create(..., stream=True)` returns an async iterator; then `async for` it. Both async forms require the `await` (same shape as the OpenAI Python SDK). Sync streaming returns an iterator directly.
- **BYO-header auth for `/api_keys/generate_web3_key` + `/x402/*`** — these routes use wallet signatures (SIWE) or signed x402 payment payloads, not bearer tokens. The resources accept the header values as plain strings (`siwx_header=`, `payment_header=`) and send them verbatim with `no_auth=True` so the default bearer is stripped. We don't bundle a web3 signer; callers produce the signed payloads with their own tooling. The canonical wallet-auth header is now `SIGN-IN-WITH-X` (used by the newer `/crypto/rpc/{network}` and `/audio/voices` routes, which accept *either* bearer or wallet auth); `/x402/*` still sends the legacy `X-Sign-In-With-X` header, which Venice continues to accept.
- **Retired endpoints → deprecated stubs** — Venice answers `/billing/usage` (sunset 2026-09-16) and `/video/transcriptions` with 410. `billing.usage` / `billing.iter_usage` / `video.transcribe` are kept with their old signatures, decorated with `typing_extensions.deprecated` (runtime `DeprecationWarning` + type-checker flag), and raise `VeniceGoneError(status_code=410)` **locally, without a network call**, naming the replacement. They're removed in 1.0 (major bump). `BillingUsageResponse` / `VideoTranscriptionResponse` stay importable from `types.py` as hand-authored deprecated models (the generated `BillingUsageResponse` vanished with the spec). A real 410 from the wire also maps to `VeniceGoneError`, with `Sunset` / `Deprecation` / `Link` headers on `.sunset` / `.deprecation` / `.link`.
- **Voice changer retrieve is dual-shape** — `/audio/voice-changer/retrieve` returns JSON `{"status": "PROCESSING", …}` while running and raw `audio/mpeg` bytes once done (no JSON status on success). `voice_changer.retrieve` sends `Accept: <accept>, application/json` via `_send`, branches on the response content type, and returns one `VoiceChangerRetrieveResponse` (subclass of `AudioRetrieveResponse`): bytes land on `.audio` with a synthesized `status="COMPLETED"` and the `x-venice-*` headers parsed into fields. `queue` takes exactly one of `file=` (multipart; booleans rendered `"true"`/`"false"`) or `audio_url=` (JSON).
- **Decisions (beta)** — `client.decisions.create(model, state, questions, images=None, **extra)` posts to `/decisions`; answers are `dict[str, dict[str, Any]]` because Venice marks the shape unstable. `/systemone` is an upstream alias and deliberately not wrapped separately.
- **Crypto JSON-RPC proxy (`client.crypto`)** — `networks()` is public (`no_auth=True`, no key needed at the wire level). `rpc(network, request, …)` proxies a single JSON-RPC object or a batch list and returns the decoded JSON verbatim (`dict` or `list`) via `_request_any` — there's no typed wrapper for the RPC payload because its shape is method-dependent. Per-request JSON-RPC failures are HTTP 200 with an `error` field, not exceptions.
- **x402 top-up discovery flow** — `POST /x402/top-up` returns 402 by design when called without a payment header; that body (`x402Version` + `accepts`) is surfaced as `VeniceX402PaymentRequiredError`, not an error condition. One method (`x402.top_up`) covers both the discovery and the signed-payment flows.
- **Auto-pagination helpers** — four list endpoints (`x402.transactions`, `characters.list`, `characters.reviews`, `billing.usage_history`) ship companion `iter_*` methods (`iter_transactions`, `iter_list`, `iter_reviews`, `iter_usage_history`) that return an `AsyncPaginator` / `Paginator` and walk every page automatically. Items are `dict[str, Any]` by drift-tolerance convention (same as the single-page wrappers). The single-page methods keep working unchanged; `iter_*` is purely additive. End-of-data is detected per endpoint: `hasMore=False` (x402), `page >= totalPages` (characters.reviews), `nextCursor is None` (billing.usage_history — a cursor walk: the first request carries the filters, continuations send **only** `cursor`, and combining the two raises `ValueError` client-side), or a short page (characters.list, which has no envelope). `api_keys.rate_limits_log` is **not** paginated (swagger fixes it at last-50) so it has no `iter_*` counterpart.

## Response-model strategy

Hand-authored wrappers in `types.py` (`ModelList`, `ChatCompletionResponse`, etc.) use `list[dict[str, Any]]` for nested collections rather than strict generated types. Pydantic validates recursively, so nesting a strict schema inside a tolerant wrapper reintroduces validation fragility. Callers who need the typed nested form parse an element explicitly: `ModelResponse.model_validate(result.data[0])`.

Generated response types used directly by resources (`BillingBalanceResponse`, `ResponsesResponse`, …) use `Cls.model_construct(**raw)` rather than `model_validate` — skipping strict schema validation — so missing/renamed required fields in Venice's responses won't break the client.

## Commands

- Regenerate types: `bash scripts/regen_types.sh` (fetches latest swagger) or `--offline` (uses pinned `vendor/venice-swagger.yaml`). `--base-class veniceresch._base_model.VeniceBaseModel` is already wired in.
- Lint/format: `ruff check .` / `ruff format .`
- Type check: `mypy src/veniceresch` (strict, excludes `_generated.py`)
- Unit tests (offline, respx-mocked): `pytest` — integration tests are excluded by default via `addopts --ignore=tests/integration`.
- Integration smoke (hits real API): `VENICE_API_KEY=... pytest tests/integration -m integration`. Free/token-cheap checks run by default; tests billed per job (voice-changer round trip, min. 1 minute) also need `VENICE_INTEGRATION_PAID=1`; admin-only routes (`/billing/*` — inference keys get 401 "Admin API key required") use a separate optional `VENICE_ADMIN_API_KEY` and skip without it (the `paid` input on the manual `integration.yml` dispatch; the weekly schedule never sets it). New endpoints should get at least a free-tier live check here — the mocked suite can't catch wire drift.
- Single test: `pytest tests/test_chat.py::test_name`
- Install in editable mode: `pip install -e ".[dev]"` — and check it actually is: a stale non-editable copy in site-packages silently shadows `src/` and makes pytest test the old release (`python -c "import veniceresch; print(veniceresch.__file__)"` must point into `src/`).
- Build dists locally: `python -m build` → `python -m twine check dist/*` (mirrors what CI does).

## Releasing

Published to **public PyPI** as `veniceresch` via Trusted Publishing (OIDC) — no API token is stored in the repo. The `.github/workflows/release.yml` job fires on any `v[0-9]+.[0-9]+.[0-9]+` tag: it asserts the tag matches `project.version` in `pyproject.toml`, runs `python -m build` + `twine check`, then publishes through `pypa/gh-action-pypi-publish` from the `pypi` GitHub environment.

To cut a release: bump `version` in `pyproject.toml` (the single source of truth — `src/veniceresch/_version.py` reads it back from package metadata via `importlib.metadata`, so there is nothing else to hand-bump), update `CHANGELOG.md`, commit, then `git tag vX.Y.Z && git push --tags`. Breaking changes get a **major** bump so downstreams pinning `veniceresch>=0.5,<1.0` stay safe. One-time setup (account-side, can't be done from the repo): create the PyPI project / pending publisher pointing at owner `balresch`, repo `veniceresch`, workflow `release.yml`, environment `pypi`.

## Endpoint coverage

Covered (49 of 49 live paths, spec `20261108`): chat (1), responses (1), image (6), images (1, OpenAI alias for `/images/generations`), video (4), audio (11 — incl. `/audio/voices` voice cloning and the 4 `/audio/voice-changer/*` routes), models (3), embeddings (1), billing (3 — balance, usage-history, usage-analytics), augment (3), characters (3), api_keys (5), x402 (3), crypto (2 — `/crypto/rpc/networks` + `/crypto/rpc/{network}` JSON-RPC proxy), decisions (1, plus the `/systemone` alias). The 2 retired paths (`/billing/usage`, `/video/transcriptions`) have deprecated stubs. `/chat/completions` and `/responses` both support SSE streaming. See `CHANGELOG.md` and the coverage table in `README.md` for the full list.

## Python / packaging

- Python floor: **3.10+** (PEP 604 `X | Y` unions; `typing_extensions.Self` because `typing.Self` is 3.11+).
- Build backend: `hatchling`. PyPI name: `veniceresch`. Import: `veniceresch`.
- mypy is strict on hand-written code; `_generated.py` is explicitly excluded.
