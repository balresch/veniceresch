# Changelog

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] — unreleased

### Added

- `VeniceConnectionError` and `VeniceTimeoutError` — transport-level failures
  (DNS, TLS, connection reset, timeouts) are now wrapped and raised as
  subclasses of `VeniceError`. The underlying `httpx` exception is preserved
  on `__cause__`. Wrapping covers every `httpx` call site: both `_send`
  paths, both `_request_stream` paths, and mid-iteration drops inside
  `chat.stream` (sync + async). Closes #1.

### Changed (breaking)

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
