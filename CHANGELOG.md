# Changelog

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] — 2026-04-20

### Added

- Resource methods return typed Pydantic models instead of raw dicts.
  `chat.create` → `ChatCompletionResponse`, `chat.stream` events →
  `ChatCompletionChunk`, `chat.create_response` → `ResponsesResponse`,
  `models.list` → `ModelList`, `billing.balance` → `BillingBalanceResponse`,
  etc. All inherit from a `VeniceBaseModel` with
  `ConfigDict(extra="allow")`, so unknown fields Venice adds later don't
  raise — they land on `.model_extra`. Attribute access everywhere:
  `response.choices[0]` instead of `response["choices"][0]`. Closes #4.
- `src/venice_sdk/types.py` re-exports the generated and hand-authored
  response classes as the public types surface.
- `src/venice_sdk/_base_model.VeniceBaseModel` — shared base for every
  Pydantic model. Generated classes inherit it via
  `datamodel-codegen --base-class`. `scripts/regen_types.sh` also strips
  the per-class `extra="forbid"` overrides that datamodel-codegen emits
  for schemas with `additionalProperties: false` in the swagger.
- `client.chat.completions.create(...)` / `.stream(...)` — OpenAI-compatible
  namespace alias. `client.chat.create(...)` still works; both spellings
  delegate to the same underlying request. Closes #2.
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
- Code that previously caught `httpx.ConnectError`, `httpx.ReadTimeout`, or
  other `httpx.*` transport exceptions will stop catching them. Replace
  `except httpx.ConnectError` with `except VeniceConnectionError` (and
  `httpx.TimeoutException` with `VeniceTimeoutError`). No `httpx` imports
  are needed at call sites anymore.

## [0.1.0] — unreleased

Initial release. Replaces the abandoned community package `venice-ai`.

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
  - **Image**: `generate` / `generate_binary`, `edit`, `multi_edit`, `upscale`,
    `background_remove`, `list_styles`. **`edit` and `multi_edit` were missing
    from the community SDK.**
  - **Video**: `queue`, `retrieve`, `retrieve_binary`, `quote`, `complete`,
    `transcribe`, plus `wait_for_completion` polling helper. Raises
    `VeniceVideoTimeoutError` on deadline.
  - **Audio**: `create_speech` (TTS), `transcribe` (multipart upload),
    queue/retrieve/complete flow mirroring video, `wait_for_completion`.
  - **Models**: `list`, `list_traits`, `compatibility_mapping`. `type="video"`
    works (the community SDK's Literal excluded it).
  - **Embeddings**: `create`.
  - **Billing**: `balance`, `usage`, `usage_analytics`.
- Auto-generated Pydantic v2 models from Venice's OpenAPI spec
  (`src/venice_sdk/_generated.py`, 189 models). Regenerate with
  `bash scripts/regen_types.sh`.
- Integration smoke suite (`tests/integration/`) gated on `VENICE_API_KEY`.
- `mypy --strict` clean, `ruff` clean, 97 unit tests.

### Not yet covered

- `/images/generations` (OpenAI alias — redundant with `/image/generate`)
- `/augment/scrape`, `/augment/search`, `/augment/text-parser` — planned for v0.2
- `/characters/*` — planned for v0.2
- `/api_keys/*`, `/x402/*` — out of scope
