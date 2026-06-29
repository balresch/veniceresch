# veniceresch Backlog

Derived from the 2026-06-28 code review (`VENICERESCH_REVIEW.md`), then
fact-checked against the working tree. Each item is self-contained: a future
session should be able to pick up any single item without re-reading the review.

Items are ordered by recommended execution order (cheapest / highest-value
first), **not** by the review's original numbering. The review's original
number is noted in each title for traceability.

Status legend: `TODO` / `IN PROGRESS` / `DONE` / `WONTFIX`.

Quality gates for every item (must all pass before committing):

```
pytest -q
ruff check . && ruff format --check .
mypy src/veniceresch
```

---

## 1. Widen the binary content-type guard  (review #5)  — DONE

**Priority: highest.** Small, self-contained, closes a real silent-corruption
hole that is the same class the guard was originally built to stop.

**Problem.** `_guard_binary_content_type` in `src/veniceresch/_client.py:63-90`
only rejects a 2xx body whose content-type is exactly `application/json`:

```python
content_type = response.headers.get("content-type", "")
if content_type.split(";", 1)[0].strip().lower() != "application/json":
    return   # <-- everything non-JSON passes through as "media bytes"
```

A 2xx `text/html` / `text/plain` / `application/xml` body (CDN error page,
auth-proxy interstitial, presigned-URL error) is therefore returned verbatim as
"media bytes" — the exact silent corruption the guard exists to prevent, just
via a different content type.

**Fix.** Reject unexpected *textual* content types for binary endpoints, while
keeping genuine media (`video/mp4`, `image/png`, `audio/mpeg`,
`application/octet-stream`) and untyped/empty responses passing through.
Two viable shapes:
- Minimal: in addition to JSON, treat any `text/*` (and `application/xml`,
  `application/xhtml+xml`) 2xx body on a binary request as
  `VeniceUnexpectedContentTypeError`.
- Fuller (review's preferred): let resource methods pass an allow-list of
  acceptable binary content types into `_request_bytes`; reject anything else
  textual by default. Keep a low-level raw-bytes path for truly arbitrary
  downloads (e.g. `video.download` of a presigned URL).

Reuse the existing `VeniceUnexpectedContentTypeError` and the existing message
style in `_client.py:80-90`. The guard is called from both async and sync
`_request_bytes` (`_client.py:257` and `:468`) so a single shared helper change
covers both surfaces.

**Callers affected:** `audio.retrieve_binary` / `create_speech`,
`video.retrieve_binary` / `download`, `image` binary endpoints
(edit/multi-edit/upscale/background-remove), `image.generate_binary`.

**Tests** (`tests/`, respx-mocked): for a binary endpoint, assert that a 2xx
`text/html` body raises `VeniceUnexpectedContentTypeError`; same for
`text/plain`; assert a missing/empty `content-type` still returns bytes; assert
genuine `video/mp4` / `image/png` / `application/octet-stream` still return
bytes unchanged. Confirm the existing JSON-guard test still passes.

**Acceptance:** textual 2xx bodies on binary endpoints fail loudly; real media
and untyped bodies are unchanged; both async and sync paths covered.

---

## 2. Fix multi-line `data:` joining in the SSE parser  (review #1, descoped)  — DONE

**Note on scope.** The review framed this as a broad parser-hardening effort and
listed many "missing" cases. Fact-check: the parser in
`src/veniceresch/resources/_sse.py` *already* handles comment lines (`:` →
line 45), CRLF normalization (line 32), trailing events without a final blank
line (lines 74-81 async / 97-103 sync), and `[DONE]`. Those are present in code
but may lack dedicated tests. The **one genuine functional bug** is multi-line
`data:` handling.

**Problem.** `_parse_event` (`_sse.py:37-54`) returns on the *first* `data:`
line:

```python
for line in raw.splitlines():
    ...
    if not line.startswith("data:"):
        continue
    payload = line[len("data:"):].strip()
    if payload == _DONE_SENTINEL:
        raise _StreamDone
    return json.loads(payload)   # <-- only the first data: line in the event
```

Per the SSE spec, one event may contain multiple `data:` lines that must be
**joined with `\n`** before decoding. Venice's chat chunks are single-line today,
but a spec-compliant multi-`data:` event would currently parse only its first
line (and likely throw a `json.JSONDecodeError` on a partial fragment, surfacing
as a runtime exception mid-stream).

**Fix.** Accumulate all `data:` line payloads in the event, join with `\n`, then
`json.loads` once. Treat a `data:` line equal to `[DONE]` as the stop sentinel
regardless of position. Keep ignoring `id:` / `retry:`. Decide on `event:`
(see optional sub-item below). Apply to the single `_parse_event` helper — both
`aiter_sse_events` and `iter_sse_events` call it, so one change covers async +
sync.

**Optional sub-item (review #1 tail): preserve `event:` names for /responses.**
`/responses` streaming (`src/veniceresch/resources/responses.py`, chunk yield at
`:162` / `:245`) may eventually emit typed events. Today the parser discards
`event:`. Only do this if/when Venice actually uses event names semantically;
otherwise leave a code comment noting the deliberate omission. Do **not**
speculatively build typed-event routing now.

**Tests** (`tests/`, likely `tests/test_sse.py` or wherever SSE tests live —
grep for `aiter_sse_events`): multi-line `data:` block joins into one JSON
object; `[DONE]` as a second `data:` line still stops; plus regression tests for
the already-handled cases that currently lack coverage (comment lines, CRLF
separators, trailing event without final blank line, invalid JSON raising
cleanly). Existing split-chunk tests must keep passing.

**Acceptance:** a multi-`data:` event decodes to the correct single JSON
payload; no behavior change for current single-line Venice chunks.

---

## 3. Opt-in failure raising for `wait_for_completion`  (review #6)  — DONE

**Problem.** `wait_for_completion` returns as soon as status is not
`"PROCESSING"`:
- audio: `src/veniceresch/resources/audio.py:190-205` (async) / `:321-336` (sync)
- video: `src/veniceresch/resources/video.py` (same pattern; mirror the audio change)

So terminal failure states (`FAILED`, `CANCELLED`, `ERROR`, etc.) are returned
as if successful unless the caller inspects `.status`.

**Constraint.** The current "return on any non-PROCESSING status" behavior is
**deliberate** — it preserves unknown terminal statuses (CLAUDE.md video/audio
polling section). Do not change the default. Add behavior, don't replace it.

**Fix.** Add an opt-in `raise_on_failed: bool = False` parameter (or a separate
`wait_for_completion_strict` helper). When enabled, raise a typed error
(e.g. extend the existing `VeniceAudioTimeoutError` neighborhood with a
`VeniceAudioFailedError` / `VeniceVideoFailedError`, or reuse `VeniceAPIError`)
on known failure statuses, while still returning normally for success and
unknown-but-non-PROCESSING statuses. Apply symmetrically to audio + video,
async + sync (4 methods). Update docstrings to state the exact contract: "waits
for a *terminal* state, not necessarily a *successful* one."

**Open question — RESOLVED (2026-06-28, from `vendor/venice-swagger.yaml`).**
Venice does **not** document any failure status strings for the queue/retrieve
polling endpoints. The swagger status enums are:
- `/video/retrieve`: `PROCESSING`, `COMPLETED` (no `FAILED`/`CANCELLED`/`ERROR`).
- `/video/queue`: `QUEUED`.
- `/audio/retrieve`: `PROCESSING` only (not even `COMPLETED` is listed).

Note the casing: the resources compare against the literal uppercase
`_STATUS_PROCESSING = "PROCESSING"` (`video.py:44`, `audio.py:30`); video's
docstring/comments reference `"COMPLETED"`. (Contrast the *`/responses`* API
status enum at swagger ~2389 — `completed`/`failed`/`in_progress`/`cancelled`,
lowercase — which is a **different** endpoint and not relevant here.)

**Implication for the implementation.** Because failure strings are
undocumented, do **not** hardcode a brittle exact-match success set that would
raise on a future unknown-but-successful status. Recommended approach: when
`raise_on_failed=True`, raise only on a curated, case-insensitive **failure**
set (`{"FAILED", "CANCELLED", "CANCELED", "ERROR"}`); any other non-PROCESSING
status (including unknown ones) still returns normally, preserving the
deliberate "tolerate unknown terminal statuses" contract. This keeps the
defensive default while making the genuinely-failed cases loud. Add new typed
errors `VeniceVideoFailedError` / `VeniceAudioFailedError` next to the existing
timeout errors — which live in the **resource modules**, not `_errors.py`:
`VeniceVideoTimeoutError` at `video.py:49` and `VeniceAudioTimeoutError` at
`audio.py:35` (both subclass `VeniceAPIError`). Mirror their definition + the
module `__all__` entry, and re-export the two new classes from `__init__.py`
(see the existing timeout re-exports at `__init__.py:23-24,31,46`).

**Tests:** with `raise_on_failed=True`, a `FAILED` status raises; default
(`False`) returns the failed-status response unchanged; success path unchanged;
timeout path unchanged. Cover audio + video, async + sync.

**Acceptance:** default behavior byte-for-byte unchanged; opt-in raises on
failure terminal states; contract documented.

---

## 4. Add a coverage floor + (optional) live smoke workflow  (review #7)  — DONE

**Problem.** Coverage sits at 88% but nothing enforces it; a regression could
silently drop it. No live smoke check guards against upstream Venice drift.

**Fix (floor).** Add `fail_under` to `[tool.coverage.report]` in
`pyproject.toml:114` (set conservatively, 80–85%, below current 88% so it's a
floor not a ceiling). Wire coverage into the CI pytest step
(`.github/workflows/ci.yml:47`, currently `pytest -q`) — e.g.
`pytest --cov=veniceresch --cov-report=term-missing` so the floor is actually
checked in CI. Confirm `[tool.coverage.run]` source/omit
(`pyproject.toml:110-112`) already excludes `_generated.py` (it does).

**Fix (optional, live smoke).** Add a separate, manually-dispatched / scheduled
GitHub workflow (NOT the default PR run) that runs
`tests/integration` with a `VENICE_API_KEY` secret. Keep it tiny: models list,
one cheap text completion, and one endpoint from each important
auth/content-type family (a binary media endpoint, a multipart upload, a
wallet-auth route). Integration tests are already marked
`integration` and excluded from default runs (`pyproject.toml:104,107`).

**Tests:** n/a (this is the test infrastructure itself). Verify locally that the
floor passes at current coverage and that intentionally dropping a covered test
trips it.

**Acceptance:** CI fails if coverage falls below the floor; live workflow (if
added) is opt-in and does not run on normal PRs.

---

## 5. File-like / streaming upload support for multipart endpoints  (review #3)  — DONE

**Priority: larger effort, ergonomic rather than correctness.**

**Problem.** Upload helpers fully buffer files into memory before sending:
- audio: `_audio_file_tuple` `src/veniceresch/resources/audio.py:52-60` (`read_bytes()`)
- augment: `_augment_file_tuple` `src/veniceresch/resources/augment.py:31-38` (`read_bytes()`)
- image: `_encode_image` `src/veniceresch/resources/image.py:28-34` (base64-encodes
  bytes / `read_bytes()`)

Large media or documents create surprising memory use, and there's no documented
size expectation or file-handle option.

**Fix.**
- For the **multipart** endpoints (audio voices/transcribe, augment parse):
  accept file-like objects in the input union and pass the handle to httpx
  rather than pre-buffering. Keep `bytes` / `str` (path) / `Path` support for
  ergonomics. The input type aliases are `AudioInput`
  (`audio.py:29`) and `AugmentInput` (augment.py). httpx multipart accepts an
  open binary file object directly in the `files=` value, so the `_*_file_tuple`
  helpers can pass the handle through instead of `.read_bytes()`.
- For the **image base64 JSON** endpoints: base64 in a JSON body inherently
  requires buffering — you cannot stream it. Do **not** try to stream these;
  instead **document** the memory behavior (the input is read fully and
  base64-expands ~33%). Update the module docstring at `image.py:8-10`.

Apply symmetrically to async + sync resources.

**Tests:** for multipart endpoints, parametrize over `Path`, string path, raw
`bytes`, an open file handle (if supported), and a missing-file path (should
raise a clear error, not a cryptic one). Assert the multipart body is built
correctly in each case (respx can inspect the request).

**Acceptance:** multipart endpoints accept file-like objects without full
buffering; existing `bytes`/`str`/`Path` callers unchanged; image base64 memory
behavior documented.

---

## 6. Parity tests for sync mirrors  (review #2)  — DONE

**Done (2026-06-28).** Added `tests/test_sync_async_parity.py`: for each
non-trivial method it runs the *same* inputs through the async and sync surfaces
against the *same* respx mock and asserts the two outgoing requests are
byte-identical (URL, headers, body), normalizing only the per-request multipart
boundary. Covered: `image.multi_edit` (`model_id`→`modelId`),
`image.generate`/`generate_binary` (`return_binary` drop/force),
`audio.create_cloned_voice` (multipart + bearer **and** `siwx_header`/`no_auth`),
`audio.transcribe` (extras stringified), `audio.retrieve_binary` (Accept
override), `chat.create`/`chat.stream` (`venice_parameters` + promoted-kwarg
merge + `stream`/Accept), `x402.balance` (legacy `X-Sign-In-With-X` + `no_auth`),
`x402.top_up` (`X-402-Payment`), `crypto.rpc` (batch body + `SIGN-IN-WITH-X` +
`Idempotency-Key` + `no_auth`), `api_keys.create` (camelCase translation),
`api_keys.generate_web3_key` (`no_auth` + camelCase). Verified the harness
catches real drift by temporarily reverting the sync `modelId` translation (the
test failed) before restoring. No production code changed; purely additive test
infra, so no CHANGELOG entry (same as item #4). Trivial post-and-parse methods
are intentionally left uncovered.

**Original scope notes (kept for traceability):**

**Note on scope.** Sync/async duplication is a **deliberate** design choice
(CLAUDE.md: "Two distinct layers; they must stay distinct" / line-for-line
mirrors for inspectability). Do **not** undertake a shared-core refactor that
trades away that readability — the review's own "only if it reduces real
duplication without making resource code harder to read" caveat applies. The
pragmatic, low-risk mitigation is **parity tests**, so a fix landing in only one
surface is caught.

**Problem.** Resources mirror sync/async line-for-line (e.g. all of `audio.py`,
`video.py`, `image.py`). Coverage already shows several "missed lines" that are
sync mirrors of tested async logic. A bug fix or parameter-translation change can
land in only one surface.

**Fix.** Add parity tests for endpoint methods with **non-trivial** behavior
(parameter translation, auth quirks, body shaping) — not the trivial
post-and-parse ones. Candidates with custom logic worth pinning:
- `model_id` → `modelId` translation in `image.multi_edit` (CLAUDE.md notes this
  camelCase quirk).
- `siwx_header` / `no_auth` wallet-auth handling (audio `create_cloned_voice`
  `audio.py:90-121` / `:234-259`; x402; crypto; `api_keys.generate_web3_key`).
- `venice_parameters` passthrough in chat.
- `return_binary` forcing in `image.generate_binary`.
- `_drop_none` body construction where extras are stringified.

A practical pattern: for each such method, run the same inputs through async and
sync against the same respx mock and assert the **outgoing request** (URL,
headers, body/multipart) is identical. This catches drift without duplicating
every assertion.

**Guidance going forward:** avoid adding new sync/async-specific logic unless the
transport genuinely requires it (it rarely does beyond `await`/`asyncio.sleep`
vs `time.sleep`).

**Acceptance:** non-trivial methods have a test asserting sync and async produce
identical wire requests.

---

## 7. Document & test the deliberate `model_construct` sites  (review #4, descoped)  — DONE

**Done (2026-06-28).** Added why-comments at the augment and responses
`model_construct` sites (`augment.py` scrape/search async+sync; `responses.py`
create async+sync) explaining *why* validation is bypassed for that endpoint
(Venice drops/renames schema-required fields; large fast-moving enum/polymorphic
schema) and pointing at CLAUDE.md "Response-model strategy". Billing
(`billing.py:23`) and `ModelList.parsed_data` (`types.py:128`) were already
commented, so left unchanged. Added focused drift tests: `test_augment.py`
(`scrape` tolerates a body missing required `format`; `search` tolerates a
nested result missing required `date`, kept as a raw dict) and
`test_responses.py` (`create` tolerates an unknown `status` enum value plus a
missing required `created_at`). Each test first asserts `model_validate` raises
`ValidationError` on the same raw body — so it fails loudly if the schema ever
stops requiring those fields — then asserts the resource call round-trips the
present fields. No production behavior changed; purely comments + additive
tests, so no CHANGELOG entry (same as items #4 and #6). 265 tests pass; ruff +
mypy clean.

**Note on scope.** The review claimed this isn't a conscious choice and named
`models.py` as a culprit. Fact-check: this is **wrong**. `models.py` uses
`model_validate` everywhere. The `model_construct` strategy is already
**documented and deliberate** (CLAUDE.md "Response-model strategy": generated
response types use `model_construct(**raw)` to survive Venice dropping/renaming
required fields). `billing.py:23` already carries an explanatory comment. So
this item is mostly documentation hygiene, not a correctness fix.

**Actual `model_construct` sites** (verified):
- `src/veniceresch/resources/augment.py:50` (`WebScrapeResponse`), `:69`
  (`WebSearchResponse`) — async; `:108`, `:127` — sync.
- `src/veniceresch/resources/responses.py:112`, `:219` (`ResponsesResponse`).
- `src/veniceresch/resources/billing.py:61,84,105,148,171,192` — **already
  commented** at `:23`.

Everything else (models, video, x402, characters, embeddings, image, chat,
crypto, images, audio) uses `model_validate` — leave those alone.

**Fix.** Add a one-line comment at the augment and responses `model_construct`
sites explaining *why* validation is bypassed for that specific endpoint (Venice
known to omit/rename required fields). Add a focused test per bypassed endpoint
demonstrating the case validation would reject but `model_construct` accepts
(e.g. a response missing a generated-schema "required" field still round-trips).

**Do not** convert these to `model_validate` — that would reintroduce the
fragility the strategy deliberately avoids.

**Acceptance:** every `model_construct` resource site has a why-comment and a
test pinning the drift case it tolerates.

---

## 8. Regen-script post-generation guard  (review secondary obs.)  — DONE

**Priority: low / nice-to-have.**

**Problem.** `scripts/regen_types.sh` strips `extra="forbid"` from generated
`ConfigDict`s via regex, which depends on the exact generated formatting. If
`datamodel-codegen` changes its output format, the strip could silently miss
some classes and reintroduce `extra="forbid"` (breaking drift tolerance).

**Fix.** Add a post-generation assertion to the script: after generation, grep
`src/veniceresch/_generated.py` for `forbid` and fail the script if any remain.
Add a short comment block in the script noting what to inspect after regen, and
remind (in script output or CLAUDE.md) to run `pytest` + `mypy` before
committing regenerated types.

**Acceptance:** regen fails loudly if any generated class still forbids extras.

**Done (2026-06-28).** Added a post-generation guard to
`scripts/regen_types.sh`: after the strip + `ruff format`, it greps the
generated file for `forbid` and `exit 1`s with a remediation message if any
survive (pointing at the strip regex to update). Added a `NOTE` comment block at
the strip step explaining the regex is keyed to datamodel-codegen's exact output
formatting and that the guard catches drift in that formatting. Added a closing
reminder line to run `pytest` + `mypy src/veniceresch` before committing
regenerated types. Verified `bash -n` passes and the guard both passes on the
current clean `_generated.py` and trips on a simulated `extra="forbid"`
leftover. Pure tooling change (no production code, no types regenerated), so no
CHANGELOG entry.

---

## Secondary observations (no action / framing only)

- **Typed but not deeply typed.** Many fields are `dict[str, Any]` / `Any`
  (chat messages, choices, drift-prone endpoints) — a deliberate alpha-stage
  drift-tolerance choice. Action: keep README framing honest ("typed resource
  methods and typed response wrappers while remaining tolerant of Venice API
  drift"); don't oversell deep type safety. No code change.
- **OpenAI aliases scoping.** `client.image` (Venice-native, broader) vs
  `client.images` (OpenAI-compatible); `client.chat.create` ==
  `client.chat.completions.create`; `client.responses` is its own API. README
  mostly handles this. Action: keep the alias boundaries explicit in docs. No
  code change.
