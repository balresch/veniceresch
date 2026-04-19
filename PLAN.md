# Venice SDK — Implementation Plan

Snapshot: 2026-04-19. Written for a new agent that will build this repo from scratch.

## Why this exists

The PyPI package `venice-ai` (by third-party author Seth Bang) is abandoned:
last commit 2025-10-16, last PyPI release 2025-06-25, the `ModelType` Literal
excludes `"video"`, and none of the `image/edit`, `image/multi-edit`, or
`video/queue|retrieve` endpoints are exposed. Venice itself publishes no
official Python SDK — `github.com/veniceai` ships CLIs, docs, a MCP server,
and an x402 client, but no Python library.

What Venice *does* publish is a maintained OpenAPI 3.0 spec:
`github.com/veniceai/api-docs/blob/main/swagger.yaml` (456 KB, 41 paths,
42 schemas, version stamp is refreshed daily). That's our source of truth.

This project is a replacement SDK that:
1. Generates Pydantic models from Venice's swagger (authoritative types).
2. Wraps them in a thin hand-written `httpx` client with Venice-specific
   ergonomics (retries, auth, error mapping, `venice_parameters`).
3. Becomes a standalone PyPI package that lewdresch depends on.

## Goals and non-goals

**Goals**
- Cover 100% of the endpoints lewdresch uses today (chat, image generate,
  image edit, image multi-edit, image upscale, audio speech, video
  queue/retrieve, models list, embeddings).
- Typed request/response shapes for every endpoint in the swagger.
- Async-first API; provide sync wrappers as a thin shim.
- First-class support for `venice_parameters` (Venice-specific chat extras).
- Regenerable types: one command pulls the latest swagger and rewrites the
  type module.

**Non-goals**
- OpenAI drop-in compatibility. Venice *is* OpenAI-compatible at the HTTP
  layer, but we don't pretend to be a drop-in for the `openai` Python SDK.
- Retry/backoff logic. lewdresch already has its own retry layer; this SDK
  exposes hooks but doesn't implement retries.
- CLI or interactive tooling. This is a library only.
- Streaming parsers beyond the bare bytes (lewdresch-side can wrap).

## Open questions (decide before starting)

1. **Package name on PyPI.** `venice-ai` is taken. Candidates:
   - `venice-sdk` — clearest intent; no conflicts on PyPI as of today.
   - `venice-api` — close but `venice` prefix is heavily squatted.
   - `balresch-venice` — namespaced, avoids any ambiguity.
   - Recommendation: **`venice-sdk`** unless you want to namespace it.
2. **Import name.** Most likely `venice_sdk` matching the package name.
   Lewdresch's existing `from venice_ai import AsyncVeniceClient` will
   become `from venice_sdk import AsyncVeniceClient` (or similar).
3. **Python version floor.** lewdresch targets 3.11. This SDK should target
   the same or 3.10 to be more portable. Recommendation: **3.10+** (covers
   PEP 604 `X | Y` union types without `from __future__ import annotations`).
4. **License.** MIT matches the ecosystem (community SDKs, openai SDK, Venice
   docs repo are all MIT-compatible). Recommendation: **MIT**.
5. **Public repo?** Yes or no — doesn't affect the code but affects whether
   you can use GitHub Actions' free tier for CI.

## Project layout

```
venice_sdk/
├── PLAN.md                      # this file
├── README.md                    # repo frontdoor (see README.md stub)
├── LICENSE                      # MIT
├── pyproject.toml               # hatch or pdm build backend
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml               # lint + type-check + test on PR
│       ├── release.yml          # publish to PyPI on tag
│       └── swagger-sync.yml     # weekly cron: refetch + open PR if drift
├── vendor/
│   └── venice-swagger.yaml      # pinned copy of upstream spec
├── scripts/
│   └── regen_types.sh           # `datamodel-codegen ... vendor/venice-swagger.yaml → src/venice_sdk/_generated.py`
├── src/
│   └── venice_sdk/
│       ├── __init__.py          # re-exports VeniceClient, AsyncVeniceClient, types, errors
│       ├── _client.py           # low-level httpx wrapper (sync + async)
│       ├── _errors.py           # typed exceptions + status-code mapper
│       ├── _generated.py        # AUTO-GENERATED from swagger (checked in)
│       ├── py.typed             # PEP 561 marker
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── chat.py          # /chat/completions + /responses
│       │   ├── image.py         # /image/*
│       │   ├── video.py         # /video/* (queue + retrieve helper)
│       │   ├── audio.py         # /audio/*
│       │   ├── models.py        # /models, /models/traits, /models/compatibility_mapping
│       │   ├── embeddings.py    # /embeddings
│       │   ├── billing.py       # /billing/*
│       │   └── characters.py    # /characters (skip for v1 if time-boxed)
│       └── types.py             # re-exports curated types from _generated
└── tests/
    ├── conftest.py              # respx fixtures
    ├── test_chat.py
    ├── test_image.py
    ├── test_video.py
    ├── test_audio.py
    ├── test_models.py
    ├── test_embeddings.py
    ├── test_errors.py
    └── integration/
        └── test_live.py         # gated on VENICE_API_KEY env var
```

## Technology choices

| Choice | Pick | Why |
|---|---|---|
| HTTP client | `httpx` (>= 0.27) | Async-first, mature; same lib lewdresch already uses |
| Validation | `pydantic` v2 | Typed request/response bodies from the generator; strict-by-default |
| Type generator | `datamodel-code-generator` | Swagger/OpenAPI → Pydantic v2 models; battle-tested, actively maintained |
| Build backend | `hatchling` | Minimal, standard, no extra config files |
| Lint/format | `ruff` | Matches lewdresch; fast |
| Type check | `mypy --strict` | Matches lewdresch |
| Test runner | `pytest` + `pytest-asyncio` + `respx` | `respx` mocks httpx transparently; no live calls in unit tests |
| CI | GitHub Actions | Free for public repos; OIDC for PyPI trusted publishing |

## API design

### Client

```python
from venice_sdk import AsyncVeniceClient

async with AsyncVeniceClient(api_key="...") as client:
    response = await client.chat.create_completion(
        model="claude-opus-4-7",
        messages=[{"role": "user", "content": "hi"}],
        venice_parameters={"include_venice_system_prompt": False},
    )
```

**Constructor:**

```python
class AsyncVeniceClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,         # falls back to VENICE_API_KEY env
        base_url: str = "https://api.venice.ai/api/v1",
        timeout: float = 60.0,
        http_client: httpx.AsyncClient | None = None,  # for reuse / test injection
        default_headers: dict[str, str] | None = None,
    ) -> None: ...
```

Sync equivalent: `VeniceClient` with the same shape.

### Resources

Each resource namespace is a thin class holding a reference to the client:

```python
class AsyncImageResource:
    async def generate(self, *, model: str, prompt: str, **kwargs) -> ImageResponse: ...
    async def edit(self, *, image: bytes | str, prompt: str, model: str | None = None, **kwargs) -> bytes: ...
    async def multi_edit(self, *, images: list[bytes | str], prompt: str, model_id: str, **kwargs) -> bytes: ...
    async def upscale(self, *, image: bytes | str, **kwargs) -> bytes: ...
    async def background_remove(self, *, image: bytes | str) -> bytes: ...
    async def list_styles(self) -> ImageStyleList: ...
```

All resources follow this pattern: accept kwargs matching the swagger's
`requestBody.properties`, build the payload, call `self._client._post(...)`,
parse the response into the generated Pydantic type (or return bytes for
binary responses).

### Types

Everything in `src/venice_sdk/_generated.py` is auto-generated and
re-exported selectively through `types.py`:

```python
# types.py
from venice_sdk._generated import (
    ChatCompletionRequest,
    ChatCompletionResponse,    # if the spec defines it; otherwise hand-typed
    ModelResponse,
    ModelSpec,
    # ... curated list; skip anything we don't want to expose ...
)
```

Don't re-export everything from `_generated` — that file is big and noisy.
Only expose what callers should see.

### Errors

```python
# _errors.py
class VeniceError(Exception): ...
class VeniceAPIError(VeniceError):
    status_code: int
    error_body: dict | str

class VeniceAuthError(VeniceAPIError): ...                 # 401
class VeniceInsufficientBalanceError(VeniceAPIError): ...  # 402 (DIEM exhausted)
class VeniceValidationError(VeniceAPIError): ...           # 400 / 422
class VeniceRateLimitError(VeniceAPIError): ...            # 429
class VeniceServerError(VeniceAPIError): ...               # 5xx
class VeniceContentViolationError(VeniceAPIError): ...     # per ContentViolationError schema
```

Mapping lives in `_client._raise_for_status()`. Match lewdresch's existing
exception names where possible so the migration can alias imports.

## Type generation workflow

`scripts/regen_types.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SWAGGER_URL="https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml"
VENDORED=vendor/venice-swagger.yaml
OUT=src/venice_sdk/_generated.py

curl -fsSL "$SWAGGER_URL" -o "$VENDORED"

datamodel-codegen \
  --input "$VENDORED" \
  --input-file-type openapi \
  --output "$OUT" \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.10 \
  --use-annotated \
  --use-double-quotes \
  --use-union-operator \
  --use-standard-collections \
  --field-constraints \
  --collapse-root-models \
  --disable-timestamp \
  --custom-file-header "# AUTO-GENERATED from vendor/venice-swagger.yaml. Do not edit by hand."

ruff format "$OUT"
```

- Commit `_generated.py` to the repo — users install the package and get
  types without needing the generator installed.
- The weekly `swagger-sync.yml` workflow runs this script, diffs the result,
  opens a PR if anything changed.
- Humans review the PR: new fields are usually safe to add; removed fields
  are a signal of API breakage worth investigating.

## Testing strategy

**Unit tests (respx, offline):** every resource method has a test that
mocks the exact HTTP call (method, path, body, headers) via `respx` and
asserts the parsed response. No network.

**Error-mapping tests:** feed 400/401/402/422/429/500 responses through
`_raise_for_status` and assert the right exception subclass.

**Integration tests (gated):** `tests/integration/test_live.py` hits the
real API when `VENICE_API_KEY` is set. Skipped in CI unless the secret is
configured. Keep it small (1-2 calls per resource) — this is a smoke, not
a regression suite.

**Type check:** `mypy --strict src/venice_sdk` in CI. No `Any` leaks in
the public surface.

**Coverage target:** 90%+ on hand-written code (`_client.py`, `_errors.py`,
`resources/*.py`). `_generated.py` is excluded from coverage.

## CI / release

`.github/workflows/ci.yml` (on push / PR):
- matrix: Python 3.10, 3.11, 3.12, 3.13
- `ruff check`, `ruff format --check`, `mypy --strict`, `pytest`

`.github/workflows/release.yml` (on `v*` tag):
- Build wheel + sdist
- Publish to PyPI via trusted publishing (OIDC, no API key in secrets)

`.github/workflows/swagger-sync.yml` (weekly cron):
- Run `scripts/regen_types.sh`
- If diff: create a branch, commit, open PR with the swagger diff
- Requires human review — API shape changes are deliberate signals

## Phased implementation

### Phase 1 — Scaffold (0.5 day)
- `pyproject.toml`, `.gitignore`, `LICENSE`, `README.md`
- Empty package skeleton with `py.typed`
- CI: ruff + mypy + pytest running on an empty test
- `scripts/regen_types.sh` working; `_generated.py` committed

### Phase 2 — Core client (1 day)
- `AsyncVeniceClient` + sync `VeniceClient`
- `_errors.py` with full exception hierarchy and status-code mapper
- Auth, base URL, timeout, httpx session reuse
- Tests: construction, request header injection, error mapping

### Phase 3 — Chat (1 day)
- `resources/chat.py` with `create_completion` (streaming + non-streaming)
- `venice_parameters` pass-through
- Support for `ChatCompletionContentPartVideoUrl` / `ChatCompletionContentPartInputAudio` (vision/audio input parts)
- Tests: text response, image-in message, streaming, `venice_parameters`,
  error cases

### Phase 4 — Image (0.5 day)
- `resources/image.py`: generate, edit, multi_edit, upscale,
  background_remove, list_styles
- Handle binary response bodies (upscale returns raw bytes)
- Tests: each endpoint with respx

### Phase 5 — Video (0.5 day)
- `resources/video.py`: queue, retrieve, quote, complete
- Helper `wait_for_completion(queue_id, timeout_s)` that polls `/video/retrieve` — this is the only method with actual logic beyond "post and parse"
- Tests: queue flow, poll flow, timeout, error status

### Phase 6 — Audio, models, embeddings, billing (0.5 day)
- Thin dispatchers for each
- Tests

### Phase 7 — Integration smoke + docs (0.5 day)
- `tests/integration/test_live.py` with 5-6 real calls
- `README.md` usage examples
- CHANGELOG entry for v0.1.0

### Phase 8 — First release (0.25 day)
- Tag `v0.1.0`
- PyPI trusted publishing configured
- Verify install works: `pip install venice-sdk` in a fresh venv

**Total: ~5 days of focused work for a solo agent.**

## Acceptance criteria

Release v0.1.0 is done when:
- [ ] `pip install venice-sdk` works from PyPI
- [ ] `mypy --strict` clean on the whole package
- [ ] `ruff check` clean
- [ ] All 41 endpoints from `vendor/venice-swagger.yaml` have at least one unit test
- [ ] `tests/integration/test_live.py` passes against the real API when `VENICE_API_KEY` is set
- [ ] `_generated.py` regenerates cleanly from `scripts/regen_types.sh`
- [ ] README shows a 10-line "getting started" snippet that actually runs
- [ ] Can import and call from a fresh Python venv: `AsyncVeniceClient`, `VeniceClient`, `VeniceAPIError`, `ChatCompletionRequest`, `ModelResponse`

## Lewdresch migration plan (after venice-sdk ships)

Track as a separate lewdresch backlog item (e.g., BL-050). Not part of
this project's scope, but sketched here so the design stays compatible.

### Phase A — Add dep, parallel imports (1 hour)
- Add `venice-sdk >= 0.1.0` to `pyproject.toml` alongside existing `venice-ai`
- Confirm both can coexist (different package names, different modules)
- No code changes yet

### Phase B — Migrate by resource, one commit per (1-2 days total)
Files that currently `from venice_ai import ...`:
- `src/lewdresch/venice/client.py` — swap to `AsyncVeniceClient` from `venice_sdk`
- `src/lewdresch/venice/text.py`, `vision.py`, `critic.py`, `agents/base.py` — use `client.chat.create_completion`
- `src/lewdresch/venice/image.py` — replace 3 raw-httpx bypasses with `client.image.edit` / `client.image.multi_edit`; keep `client.image.generate` (was SDK), now just a rename
- `src/lewdresch/venice/video.py` — replace 2 raw-httpx bypasses with `client.video.queue` / `client.video.retrieve`; consider using the polling helper
- `src/lewdresch/venice/audio.py` — rename `client.audio.create_speech` → `client.audio.create_speech` (resource name probably stays)
- `src/lewdresch/models/sync.py` — `client.models.list(type="video")` now works natively; remove httpx fallback
- `src/lewdresch/models/pricing.py` — same

Each commit: migrate one file, update tests that patch internals, verify
`pytest` and `lewd models sync` still work.

### Phase C — Remove dep on community SDK (15 min)
- Delete `venice-ai` from `pyproject.toml`
- `pip uninstall venice-ai`
- Confirm nothing imports `venice_ai` anywhere (`grep -r "venice_ai"`)

### Phase D — Delete lewdresch's workarounds (30 min)
- The raw-httpx calls in `venice/image.py:214,294` and `venice/video.py:300+`
  become redundant once `venice-sdk` covers those endpoints natively
- The `_probe_model_list` logic in `models/sync.py` for edit/multi-edit can be
  replaced with direct `client.models.list(type="edit")` calls — but only if
  those types are valid in Venice's API (still unconfirmed)

## References

- Swagger source: https://github.com/veniceai/api-docs/blob/main/swagger.yaml
- Live API: https://api.venice.ai/api/v1
- Venice docs: https://docs.venice.ai
- Community SDK we're replacing: https://github.com/sethbang/venice-ai
- Generator tool: https://github.com/koxudaxi/datamodel-code-generator
- Pinned spec in this repo: `vendor/venice-swagger.yaml` (456 KB, 41 paths,
  42 schemas, OpenAPI 3.0.0, version stamp `20260418.031751`)
