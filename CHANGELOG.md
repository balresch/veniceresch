# Changelog

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.6.1] — 2026-06-29

### Added

- **`VeniceJobFailedError` base exception.** `VeniceAudioFailedError` and
  `VeniceVideoFailedError` (raised by `wait_for_completion(raise_on_failed=True)`)
  now share a common `VeniceJobFailedError` base, so callers can catch both
  audio and video job failures with one `except`. The two named classes and
  their attributes (`queue_id`, `status`, `result`) are unchanged. Internally,
  the duplicated failure-status set, the `is_processing` / `is_failure_status`
  predicates, and the error body now live once in `resources/_polling.py`
  instead of being copied between the audio and video resources.

### Fixed

- **Async uploads / image encodes no longer block the event loop on file reads.**
  The 0.6.0 file-like upload support streamed a synchronous file handle into
  httpx's async multipart encoder, which iterates it with blocking `.read()`
  calls *inside* the request coroutine — so a large upload to `/audio/voices`,
  `/audio/transcriptions`, or `/augment/text-parser` stalled every other
  coroutine for the whole request. Likewise the image base64 endpoints
  (`edit` / `multi_edit` / `upscale` / `background_remove`) did the path read +
  base64 on the loop. The async surfaces now offload the blocking read (and, for
  images, the base64) to a worker thread via `asyncio.to_thread` (new
  `async_open_upload` helper in `resources/_uploads.py` and `_encode_image_async`
  in `resources/image.py`). The async path trades streaming for a buffered read
  to keep the loop free; the wire output is byte-identical. Sync surfaces are
  unchanged, and `bytes` inputs stay zero-copy on both.
- **Binary content-type guard no longer rejects real media or expected text.**
  The 0.6.0 guard raised `VeniceUnexpectedContentTypeError` for *any* textual
  2xx body on a binary request, which over-rejected two legitimate cases:
  `video.download()` of a presigned/CDN URL (object stores routinely serve real
  media as `text/plain` when no `Content-Type` metadata is set) and
  `augment.parse_text` (locked to `text/plain` only). The guard now honors the
  request's `Accept` header — a body whose content type the caller explicitly
  asked for is not "unexpected" and passes through (with `*/*` and `type/*`
  wildcard support). `video.download()` fetches presigned URLs as opaque
  downloads that skip the guard entirely (a presigned URL is an object-store
  handle, not a Venice API surface). Genuine error pages on binary endpoints
  (a `text/html` body where only media was requested) still fail loudly, so the
  original silent-corruption protection is intact. The single-consumer
  `allowed_content_types` parameter on the internal `_request_bytes` helper is
  removed in favor of the `Accept`-header rule.
- **`wait_for_completion`'s in-progress check is now case-insensitive.**
  `video.wait_for_completion` / `audio.wait_for_completion` (async and sync)
  compared the poll status against an exact-match uppercase `"PROCESSING"`, so a
  `"processing"` / `"Processing"` variant looked terminal and could end the wait
  mid-job (the caller then downloaded an unfinished asset). The in-progress
  comparison is now case-insensitive, matching the already case-insensitive
  failure check in the same method. The set of statuses treated as *terminal* is
  unchanged ("anything not processing"), so tolerance of unknown terminal
  statuses is preserved.

## [0.6.0] — 2026-06-29

### Added

- **File-like inputs for upload endpoints.** The multipart upload methods
  (`audio.transcribe`, `audio.create_cloned_voice`, `augment.parse`,
  `augment.parse_text`) and the base64 image methods (`image.edit`,
  `image.multi_edit`, `image.upscale`, `image.background_remove`) now accept a
  binary file-like object (anything with `.read()`, e.g. an open `"rb"` handle,
  `io.BytesIO`, or a framework `UploadedFile`) in addition to the existing
  `bytes` / `str` path / `pathlib.Path` forms. For the multipart endpoints,
  paths and file-like objects are now **streamed** to the server via httpx
  instead of read fully into memory first (`Path.read_bytes()`); a
  caller-supplied handle is streamed and left open (the caller owns its
  lifecycle), while a path the SDK opens is closed once the request completes.
  The image endpoints still buffer in full because they send base64 in a JSON
  body, which has no streaming path — pass an `https://` URL to skip uploading
  large local files. A new shared `resources/_uploads.open_upload` helper backs
  the multipart paths, removing the duplicated per-resource file-tuple builders.
- **Opt-in failure raising for `wait_for_completion`.** `video.wait_for_completion`
  and `audio.wait_for_completion` (async and sync) gained a
  `raise_on_failed: bool = False` parameter. The default is unchanged — the
  helper still returns the final retrieve response for *any* non-PROCESSING
  status, preserving tolerance of undocumented terminal statuses. With
  `raise_on_failed=True` a known failure status (case-insensitive `FAILED` /
  `CANCELLED` / `CANCELED` / `ERROR`) instead raises the new
  `VeniceVideoFailedError` / `VeniceAudioFailedError` (the final response is on
  the error's `.result`); success and any other unknown-but-non-PROCESSING
  status still return normally. The two new error classes are exported from the
  package root. Venice does not document failure status strings for the
  queue/retrieve endpoints, so the failure set is curated rather than derived
  from a success allow-list, keeping unknown terminal statuses non-fatal.

### Fixed

- **Binary endpoints now reject *all* unexpected textual 2xx bodies, not just
  JSON.** `_guard_binary_content_type` previously only tripped on an exact
  `application/json` content type, so a 2xx `text/html` / `text/plain` /
  `application/xml` body (a CDN error page, an auth-proxy interstitial, a
  presigned-URL error) was returned verbatim as "media bytes" — the same silent
  corruption the guard exists to prevent. Such textual bodies now raise
  `VeniceUnexpectedContentTypeError`; genuine media (`video/mp4`, `image/png`,
  `audio/mpeg`, `application/octet-stream`, …) and untyped/empty responses are
  unchanged. Endpoints that legitimately return text (`augment.parse_text`,
  which expects `text/plain`) opt in via a new internal `allowed_content_types`
  allow-list. Covers both async and sync paths.
- **SSE parser now joins multi-line `data:` events before decoding.** Per the
  SSE spec a single event may carry multiple `data:` lines that must be joined
  with `\n` and decoded once; `_parse_event` previously returned on the *first*
  `data:` line, so a spec-compliant multi-`data:` event would decode only its
  first fragment (and typically raise `json.JSONDecodeError` mid-stream on the
  partial JSON). It now accumulates every `data:` line in the block, joins with
  `\n`, and `json.loads` once. A `data:` line equal to `[DONE]` stops iteration
  regardless of position. No behavior change for Venice's current single-line
  chunks. Covers both async and sync paths.

## [0.5.4] — 2026-06-21

### Fixed

- **`__version__` and the `User-Agent` header now report the real version.**
  The version was duplicated in `pyproject.toml` and a hand-bumped
  `src/veniceresch/_version.py`; the latter was missed in the 0.5.3 release, so
  installs of 0.5.3 reported `veniceresch.__version__ == "0.5.2"` and sent
  `User-Agent: veniceresch-python/0.5.2`. `_version.py` now derives the version
  from the installed package metadata (`importlib.metadata`), making
  `pyproject.toml` the single source of truth so it can't drift again.

## [0.5.3] — 2026-06-21

### Added

- **`video.download(model, queue_id, download_url=...)`** (sync + async) — new
  optional `download_url` parameter. VPS-backed `-private` models do not expose
  the media URL on `/video/retrieve` at all; the only handle is the
  `download_url` on the `video.queue()` submit response
  (`VideoQueueResponse.download_url`). Passing it makes `download()` fetch the
  media directly (presigned URL, auth stripped) and skip `/video/retrieve`
  entirely, so `download()` now cleanly covers every model family without
  callers reaching into the private `_request_bytes`. (#8)

### Fixed

- **Corrected the `VideoRetrieveResponse` docstring** (and the `video` module /
  `retrieve_binary` docstrings) which wrongly claimed VPS-backed models populate
  `download_url` on `/video/retrieve` completion. They do not — that endpoint is
  status-polling only; the media URL lives on the `video.queue()` submit
  response. (#7)

## [0.5.2] — 2026-06-20

### Fixed

- **`video.retrieve_binary` no longer returns JSON as bogus "MP4 bytes".**
  VPS-backed video models (the `-private` grok models) answer `/video/retrieve`
  with a JSON status object even when `Accept: video/mp4` is sent. The binary
  helpers previously returned that body verbatim, so a completed job yielded an
  ~81-byte JSON blob written to disk as an unplayable `.mp4` with no error.
  `_request_bytes` now inspects the response `Content-Type` and raises the new
  `VeniceUnexpectedContentTypeError` when a binary request gets a JSON body
  (the parsed JSON is on `error_body`, the offending type on `content_type`).
  This guard protects every binary endpoint (image/audio too), not just video.

### Added

- **`video.download(model, queue_id)`** (sync + async) — returns the MP4 bytes
  for a completed video for *both* model families. It calls `retrieve_binary`
  (one request for direct-bytes models) and, when that surfaces a VPS-backed
  JSON body, reads the `download_url` from it and GETs the media directly
  (with auth stripped, since those URLs are presigned). Prefer it over
  `retrieve_binary` unless you know you have a direct-bytes model.
- `VeniceUnexpectedContentTypeError` exported from the package root.
- `download_url` is now a declared field on `VideoRetrieveResponse`.

### Internal

- `_request_bytes` gained a `no_auth` passthrough (used by `download` to fetch
  presigned CDN URLs without the Venice bearer).
- Bumped `_version.__version__` to match `pyproject` (it had drifted to 0.5.0).

## [0.5.1] — 2026-06-18

### Packaging

- First release published to **public PyPI** as `veniceresch` — downstream
  projects can now depend on a version range (e.g. `veniceresch>=0.5,<1.0`)
  instead of a pinned git commit. No code or API changes from 0.5.0.
- Added `.github/workflows/release.yml`: on every `vX.Y.Z` tag it verifies
  the tag matches `project.version`, builds the sdist + wheel, runs
  `twine check`, and publishes via PyPI Trusted Publishing (OIDC) — no API
  token stored in the repo.
- Added `build` + `twine` to the `dev` extra for local release dry-runs.

## [0.5.0] — 2026-06-17

### Added

- Synced to Venice OpenAPI spec `20260617` (was `20260418`). Endpoint
  coverage: **41 → 44 paths**.
- `client.crypto.*` — JSON-RPC proxy. `networks()` lists supported network
  slugs (`GET /crypto/rpc/networks`, public/no-auth); `rpc(network, request,
  siwx_header=…, idempotency_key=…)` proxies a single JSON-RPC 2.0 object or
  a batch list of up to 100 (`POST /crypto/rpc/{network}`). Return mirrors
  the request shape — `dict` for single, `list` for batch. Per-request
  JSON-RPC errors come back as HTTP 200 items, not exceptions. New
  `CryptoRpcNetworksResponse` type.
- `client.audio.create_cloned_voice(file=…, model=…, siwx_header=…)` —
  voice cloning (`POST /audio/voices`, multipart). Returns a `vv_<id>`
  handle (`ClonedVoiceResponse`) to reuse as the `voice` argument of
  `create_speech` with the same model.
- `VenicePayloadTooLargeError` (413) and `VeniceProviderContentPolicyError`
  (422, detected by `error.type == "provider_content_policy"`; carries
  `.recommended_model` and `.credits_refunded`) — new exceptions. The latter
  is distinct from `VeniceContentViolationError` (Venice's own safety layer,
  keyed on `suggested_prompt`).
- New endpoints accept the canonical `SIGN-IN-WITH-X` wallet-auth header
  (x402). The existing `client.x402.*` methods keep the still-accepted
  legacy `X-Sign-In-With-X` header.
- Internal `no_auth=True` kwarg added to the client's `_request_any` helper
  (already on `_request_json`) — needed for the public/wallet crypto routes.

## [0.4.0] — 2026-04-21

### Added

- `client.api_keys.*` — `list`, `get(id)`, `create`, `update`, `delete`,
  `rate_limits`, `rate_limits_log`, `generate_web3_key_challenge`,
  `generate_web3_key`. Bearer-auth endpoints require an **admin**-scope
  key; the two `generate_web3_key` methods skip auth (Venice's swagger
  marks them `security: []`). Body / query keys follow the existing
  snake_case → camelCase convention (`api_key_type → apiKeyType`,
  `consumption_limit → consumptionLimit`, `expires_at → expiresAt`).
- `client.x402.*` — `balance(wallet_address, siwx_header=…)`,
  `top_up(payment_header=…)`, `transactions(wallet_address, siwx_header=…,
  limit, offset)`. Wallet-signed payloads (SIWE / x402) are passed in as
  plain strings and forwarded verbatim; this SDK doesn't bundle a wallet
  signer.
- `VeniceX402PaymentRequiredError` — new exception surfaced when a 402
  response carries the x402 discovery payload (`x402Version` + `accepts`).
  Calling `client.x402.top_up()` without a payment header raises this so
  callers can read `.accepts` to pick a payment option and retry with
  `top_up(payment_header=…)`. Non-x402 402 responses still raise
  `VeniceInsufficientBalanceError`.
- New public response types in `veniceresch.types`:
  `ApiKeyListResponse`, `ApiKeyDetailResponse`, `ApiKeyCreateResponse`,
  `ApiKeyUpdateResponse`, `ApiKeyDeleteResponse`,
  `ApiKeyRateLimitsResponse`, `ApiKeyRateLimitLogsResponse`,
  `Web3KeyChallengeResponse`, `Web3KeyCreateResponse`,
  `X402BalanceResponse`, `X402TopUpResponse`, `X402TransactionsResponse`.
- Endpoint coverage: 33 of 41 paths → **41 of 41**. Full parity with the
  current Venice OpenAPI spec.
- Internal `no_auth=True` kwarg on the client's `_request_json` / `_send`
  helpers — strips the default `Authorization: Bearer …` header when a
  route uses another auth scheme.
- Auto-paginating `iter_*` helpers for the four Venice list endpoints
  that previously required driving `limit`/`offset` or `page`/`pageSize`
  loops by hand: `client.x402.iter_transactions`,
  `client.characters.iter_list`, `client.characters.iter_reviews`, and
  `client.billing.iter_usage`. Each returns an
  `AsyncPaginator[dict, ResponseT]` (sync: `Paginator[...]`); iterating
  it yields one record at a time across page boundaries, and
  `.iter_pages()` yields the raw response per page. Iteration is lazy —
  no HTTP call fires before `async for` / `for` starts. End-of-data is
  detected per endpoint: `hasMore=False` for x402, `page >= totalPages`
  for billing.usage and characters.reviews, and "short page" for
  characters.list (which has no pagination envelope).
  `api_keys.rate_limits_log` has no `iter_*` counterpart — Venice's
  swagger fixes it at the last 50 entries with no pagination params.
  The existing single-page methods (`transactions`, `list`, `reviews`,
  `usage`) are unchanged; `iter_*` is strictly additive.
- `veniceresch.pagination.AsyncPaginator` and
  `veniceresch.pagination.Paginator` — new generic classes, also
  re-exported from top-level as `from veniceresch import
  AsyncPaginator, Paginator` for use in caller type hints.
- `ModelList.parsed_data()` — convenience method returning
  ``.data`` elements as typed :class:`ModelResponse` objects via
  ``model_construct`` (drift-tolerant; unknown fields land on
  ``.model_extra``). The raw ``.data`` field is unchanged; this is
  purely additive opt-in for typed attribute access.

## [0.3.0] — 2026-04-21

### Added

- `client.augment.*` — `scrape`, `search`, `parse`, `parse_text`. The
  parser is split into two methods mirroring the
  `image.generate` / `image.generate_binary` pattern: `parse()` returns
  a typed `TextParserResponse` (`{text, tokens}`) from the JSON form,
  `parse_text()` returns a plain `str` (multipart upload forced to
  `response_format=text`, `Accept: text/plain`).
- `client.characters.*` — `list`, `get(slug)`, `reviews(slug)`. Query
  params accept snake_case and translate to the camelCase Venice
  expects (`is_adult → isAdult`, `sort_by → sortBy`, `page_size →
  pageSize`, etc.) — same convention as `model_id → modelId` for image
  multi-edit. Boolean filters (`is_adult` / `is_pro` / `is_web_enabled`)
  are serialized as the string enum Venice requires (`"true"` /
  `"false"`).
- `client.responses.stream(...)` and
  `client.responses.create(..., stream=True)` — SSE streaming for the
  Responses API. Same await-then-`async for` contract as
  `client.chat.stream`. New public type
  `veniceresch.types.ResponsesChunk` (tolerant — Venice's swagger
  documents SSE support but doesn't define a per-chunk schema, so
  unknown fields land on `.model_extra`).
- `client.images.generate(...)` — drop-in alias for
  `openai.images.generate`. Hits Venice's `/images/generations`
  OpenAI-compatible endpoint. Coexists with the existing
  `client.image.*` (singular) namespace, which stays the primary
  Venice-native image surface. New public type
  `veniceresch.types.OpenAIImageResponse`. The generated
  `SimpleGenerateImageRequest` is re-exported from
  `veniceresch.types` for callers that want the typed request form.
- New public response types in `veniceresch.types`:
  `TextParserResponse`, `CharacterListResponse`, `CharacterDetailResponse`,
  `CharacterReviewsResponse`, `ResponsesChunk`, `OpenAIImageResponse`.
  Plus re-exports of the generated request/response types
  `WebScrapeRequest`, `WebScrapeResponse`, `WebSearchRequest`,
  `WebSearchResponse`, `SimpleGenerateImageRequest`.
- Endpoint coverage: 26 of 41 paths → 33 of 41 paths.
- Tighter return types for video and audio queue/retrieve endpoints.
  `client.video.queue/retrieve/quote/complete/transcribe` and
  `client.audio.queue/retrieve/quote/complete/transcribe` now return
  typed Pydantic models (`VideoQueueResponse`, `VideoRetrieveResponse`,
  `AudioQueueResponse`, `AudioTranscriptionResponse`, etc.) instead of
  `dict[str, Any]`. Attribute access on `.queue_id`, `.status`,
  `.text`, `.transcript`, etc. `wait_for_completion` returns
  `VideoRetrieveResponse` / `AudioRetrieveResponse`.
- `chat.create` / `chat.stream` signature promotes the common
  OpenAI-compatible fields to named kwargs for IDE autocomplete:
  `temperature`, `top_p`, `n`, `stop`, `max_tokens`,
  `frequency_penalty`, `presence_penalty`, `seed`, `tools`,
  `tool_choice`, `response_format`, `logprobs`. All previously worked
  via `**extra`; behavior is unchanged for existing callers. Less
  common Venice-specific fields (`min_p`, `repetition_penalty`,
  `reasoning_effort`, `prompt_cache_key`, etc.) still flow through
  `**extra`.

### Changed (breaking)

- `client.video.queue`, `client.video.retrieve`, `client.video.quote`,
  `client.video.complete`, `client.video.transcribe`,
  `client.video.wait_for_completion`, and every `client.audio.*`
  counterpart now return Pydantic models rather than `dict[str, Any]`.
  Callers that did `result["queue_id"]` / `result.get("status")` must
  switch to `result.queue_id` / `result.status`. Unknown fields still
  land on `.model_extra` via ``extra="allow"``.

## [0.2.0] — 2026-04-20

### Added

- Resource methods return typed Pydantic models instead of raw dicts.
  `chat.create` → `ChatCompletionResponse`, `chat.stream` events →
  `ChatCompletionChunk`, `responses.create` → `ResponsesResponse`,
  `models.list` → `ModelList`, `billing.balance` → `BillingBalanceResponse`,
  etc. All inherit from a `VeniceBaseModel` with
  `ConfigDict(extra="allow")`, so unknown fields Venice adds later don't
  raise — they land on `.model_extra`. Attribute access everywhere:
  `response.choices[0]` instead of `response["choices"][0]`. Closes #4.
- `src/veniceresch/types.py` re-exports the generated and hand-authored
  response classes as the public types surface.
- `src/veniceresch/_base_model.VeniceBaseModel` — shared base for every
  Pydantic model. Generated classes inherit it via
  `datamodel-codegen --base-class`. `scripts/regen_types.sh` also strips
  the per-class `extra="forbid"` overrides that datamodel-codegen emits
  for schemas with `additionalProperties: false` in the swagger.
- `client.chat.completions.create(...)` / `.stream(...)` — OpenAI-compatible
  namespace alias. `client.chat.create(...)` still works; both spellings
  delegate to the same underlying request. Closes #2.
- `client.responses.create(...)` — Venice's ``/responses`` endpoint
  (OpenAI-style Responses API) now has its own top-level namespace, matching
  the `openai` Python SDK's shape. Closes #5.
- `client.chat.create(stream=True)` now returns an async iterator of
  decoded SSE events. Replaces the old `ValueError`. Same shape as the
  OpenAI Python SDK. Closes #3.
- `VeniceConnectionError` and `VeniceTimeoutError` — transport-level failures
  (DNS, TLS, connection reset, timeouts) are now wrapped and raised as
  subclasses of `VeniceError`. The underlying `httpx` exception is preserved
  on `__cause__`. Wrapping covers every `httpx` call site: both `_send`
  paths, both `_request_stream` paths, and mid-iteration drops inside
  `chat.stream` (sync + async). Closes #1.

### Changed (breaking)

- Resource methods return Pydantic models, not dicts. Callers that did
  `response["id"]` must switch to `response.id`. Nested list/dict values
  (e.g. `choices`, `messages[0]["content"]`) are still plain dicts for
  drift tolerance — parse to a typed form explicitly when you need it
  (`ModelResponse.model_validate(result.data[0])`). Part of #4.
- `client.chat.stream(...)` is now an `async def` returning an async
  iterator. Callers must `await` it before `async for` — `stream =
  await client.chat.stream(...); async for e in stream: ...`. This unifies
  the contract with `create(stream=True)`. Sync `chat.stream(...)` is
  unaffected. Part of #3.
- `chat.create(stream=True)` no longer raises `ValueError`. Callers that
  caught that error to fall back to `.stream(...)` can delete the
  fallback.
- `client.chat.create_response(...)` is gone. Call
  `client.responses.create(...)` instead — same kwargs, same response
  type (`ResponsesResponse`). Part of #5.
- Code that previously caught `httpx.ConnectError`, `httpx.ReadTimeout`, or
  other `httpx.*` transport exceptions will stop catching them. Replace
  `except httpx.ConnectError` with `except VeniceConnectionError` (and
  `httpx.TimeoutException` with `VeniceTimeoutError`). No `httpx` imports
  are needed at call sites anymore.

## [0.1.0] — 2026-04-19

Initial release.

### Added

- `AsyncVeniceClient` and `VeniceClient` with API-key auth, base URL override,
  timeout config, and injectable `httpx.Client` / `httpx.AsyncClient`.
- Typed exception hierarchy: `VeniceAPIError`, `VeniceAuthError`,
  `VeniceInsufficientBalanceError`, `VeniceValidationError`,
  `VeniceNotFoundError`, `VeniceRateLimitError`, `VeniceServerError`,
  `VeniceContentViolationError` (detected by body shape, not status).
- Resources covering 26 endpoints across chat, image, video, audio, models,
  embeddings, and billing. Specifically:
  - **Chat**: `client.chat.create`, `client.chat.stream` (SSE),
    `client.chat.create_response` (`/responses`). `venice_parameters`
    pass-through.
  - **Image**: `generate` / `generate_binary`, `edit`, `multi_edit`,
    `upscale`, `background_remove`, `list_styles`.
  - **Video**: `queue`, `retrieve`, `retrieve_binary`, `quote`, `complete`,
    `transcribe`, plus `wait_for_completion` polling helper. Raises
    `VeniceVideoTimeoutError` on deadline.
  - **Audio**: `create_speech` (TTS), `transcribe` (multipart upload),
    queue/retrieve/complete flow mirroring video, `wait_for_completion`.
  - **Models**: `list`, `list_traits`, `compatibility_mapping`.
  - **Embeddings**: `create`.
  - **Billing**: `balance`, `usage`, `usage_analytics`.
- Auto-generated Pydantic v2 models from Venice's OpenAPI spec
  (`src/veniceresch/_generated.py`, 189 models). Regenerate with
  `bash scripts/regen_types.sh`.
- Integration smoke suite (`tests/integration/`) gated on `VENICE_API_KEY`.
- `mypy --strict` clean, `ruff` clean, 97 unit tests.

### Not yet covered

- `/images/generations` (OpenAI alias — redundant with `/image/generate`)
- `/augment/scrape`, `/augment/search`, `/augment/text-parser`
- `/characters/*`
- `/api_keys/*`, `/x402/*` — out of scope
