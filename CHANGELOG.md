# Changelog

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
