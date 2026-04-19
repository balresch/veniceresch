# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A typed, async-first Python SDK for the Venice.ai API. Replaces the abandoned community package `venice-ai` (by Seth Bang, `github.com/sethbang/venice-ai`). Venice publishes no official Python SDK but does maintain an OpenAPI 3.0 spec at `github.com/veniceai/api-docs/blob/main/swagger.yaml` — that spec is the source of truth for types.

Primary consumer: `github.com/balresch/lewdresch`. Design decisions should favor that migration path.

`PLAN.md` has the original design document. `CHANGELOG.md` tracks what shipped.

## Architecture — the split that matters

Two distinct layers; they must stay distinct:

1. **`src/venice_sdk/_generated.py`** — auto-generated from `vendor/venice-swagger.yaml` by `datamodel-code-generator`. **Never hand-edit.** Regenerate via `bash scripts/regen_types.sh [--offline]`. Committed so installs don't need the generator. mypy/ruff ignore it.
2. **Hand-written thin layer**:
   - `_client.py` — `AsyncVeniceClient` + `VeniceClient` (httpx wrapper). Both own their httpx session by default; callers can inject one for reuse. Internal helpers: `_request_json` (JSON in/out), `_request_any` (arrays), `_request_bytes` (binary responses), `_request_stream` (SSE / streaming).
   - `_errors.py` — typed exception hierarchy. `raise_for_response()` maps non-2xx responses. Content-violation detection by body shape (`suggested_prompt`), not status, because Venice has used both 400 and 422 for them.
   - `resources/*.py` — one module per endpoint group. Each method maps swagger `requestBody.properties` to kwargs, calls the client helper, returns a `dict[str, Any]` or `bytes`. Resources don't construct httpx requests directly.

`client.chat`, `client.image`, `client.video`, `client.audio`, `client.models`, `client.embeddings`, `client.billing` are wired in both client constructors.

## Non-goals

- **No retry/backoff logic.** lewdresch has its own retry layer; we only raise typed exceptions so callers can dispatch.
- **No OpenAI drop-in compat.** Venice is OpenAI-compatible at the HTTP layer, but this SDK doesn't mimic the `openai` package's shape.
- **No CLI.** Library only.
- **No SSE parsers beyond plain dict events.** `resources/_sse.py` stops at `[DONE]` and yields decoded JSON.

## Venice-specific ergonomics

- **`venice_parameters`** — Venice extends chat completions with an extras object. First-class kwarg in `chat.create` / `chat.stream`.
- **Binary responses** — image edit/multi-edit/upscale/background-remove return raw PNG bytes. Resource methods return `bytes`. For image-generate, `generate()` returns dict (JSON) and `generate_binary()` returns bytes (forces `return_binary=True`).
- **Video polling** — `/video/queue` gives a `queue_id`; caller polls `/video/retrieve` until `status != "PROCESSING"`. The `wait_for_completion(queue_id, model, timeout_s, poll_interval_s)` helper is the only resource method with real logic beyond "post and parse." Raises `VeniceVideoTimeoutError` on deadline. Audio has the same pattern.
- **`model_id` vs `model`** — `/image/multi-edit` uses `modelId` (camelCase) in the spec; the Python API accepts `model_id` and translates. Everywhere else it's `model`.
- **Binary Accept header** — `_request_bytes` sets `Accept: application/octet-stream` by default, but caller-provided `headers={"Accept": ...}` wins. Needed for `video/mp4`, `audio/mpeg`, etc.

## Commands

- Regenerate types: `bash scripts/regen_types.sh` (fetches latest swagger) or `--offline` (uses pinned `vendor/venice-swagger.yaml`).
- Lint/format: `ruff check .` / `ruff format .`
- Type check: `mypy src/venice_sdk` (strict, excludes `_generated.py`)
- Unit tests (offline, respx-mocked): `pytest` — integration tests are excluded by default via `addopts --ignore=tests/integration`.
- Integration smoke (hits real API): `VENICE_API_KEY=... pytest tests/integration -m integration`
- Single test: `pytest tests/test_chat.py::test_name`
- Install in editable mode: `pip install -e ".[dev]"`

## Endpoint coverage

Covered (26 of 41 paths): chat (2), image (6), video (5), audio (6), models (3), embeddings (1), billing (3). See `CHANGELOG.md` and the coverage table in `README.md` for the full list.

Deferred to v0.2 or out of scope: `/augment/*` (3), `/characters/*` (3), `/images/generations` (OpenAI alias), `/api_keys/*` (5), `/x402/*` (3).

## Python / packaging

- Python floor: **3.10+** (PEP 604 `X | Y` unions; `typing_extensions.Self` because `typing.Self` is 3.11+).
- Build backend: `hatchling`. PyPI name: `venice-sdk`. Import: `venice_sdk`.
- mypy is strict on hand-written code; `_generated.py` is explicitly excluded.
