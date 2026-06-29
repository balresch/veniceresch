# veniceresch Backlog

Items #1–#8 derive from the 2026-06-28 code review (`VENICERESCH_REVIEW.md`);
items #9–#13 derive from a 2026-06-29 review of the `v0.5.4..v0.6.0` release
(see that section's header). All are fact-checked against the working tree. Each
item is self-contained: a future session should be able to pick up any single
item without re-reading the review.

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

## 0.6.0 review (2026-06-29)

Derived from a high-effort multi-agent review of the `v0.5.4..v0.6.0` diff,
fact-checked against the working tree. Several of these are **regressions
introduced by the 0.6.0 fixes for items #1–#3 above** — the hardening landed,
but a few guards are now stricter than Venice's actual wire behavior. Same
self-contained / ordered-by-value convention as items #1–#8.

---

## 9. Stop the binary content-type guard from rejecting real media / text endpoints  (0.6.0 #1, #2, #8)  — DONE

**Done (2026-06-29).** Took the hybrid the item describes. The guard
(`_client.py`) now honors the request's `Accept` header via a new
`_request_accepts(request, main_type)` helper (exact match + `*/*` and `type/*`
wildcards): a 2xx body whose content type the caller explicitly asked for is not
"unexpected" and passes through, textual or not. This captures the real rule the
per-endpoint allow-list only gestured at, so `allowed_content_types` is **deleted**
from `_guard_binary_content_type` and both `_request_bytes` overloads (closes
0.6.0 #8). `augment.parse_text` keeps advertising `Accept: text/plain` and now
passes the guard with no special-casing — a comment notes that accepting more
textual forms is a one-line `Accept` change. For Problem A, `video.download()`'s
two presigned-URL fetches (async + sync) now pass `guard_content_type=False`: a
presigned object-store URL is an opaque download, not a Venice API surface, so
`text/plain`-labeled real MP4 bytes return rather than raise. Problem B was left
conservative — no live evidence Venice returns `text/markdown`/`text/html` from
`parse_text`, and an existing test treats `text/html` there as a bad interstitial;
the `Accept`-header mechanism makes widening trivial if evidence appears. Item #1's
guarantee is intact: a `text/html` error page on an endpoint that only asked for
media still raises. Added tests: presigned-URL download returns `text/plain` /
`text/html` / `application/xml`-labeled bytes (async parametrized + sync + the
JSON-fallback path), sync `parse_text` parity; updated the `parse_text` raises-on-
unexpected-textual comment. 271 tests pass; ruff + mypy clean. **Decision-needed
note (carried forward):** confirm against the live API (item #4 smoke workflow)
whether `parse_text` ever returns non-`text/plain` textual types before widening
its `Accept` header.

**Priority: highest.** This is a behavioral regression in the exact path item #1
hardened: the guard now over-rejects, turning previously-working downloads and
text-extraction calls into exceptions. Resolving it also dissolves the
single-consumer `allowed_content_types` special case (0.6.0 #8).

**Background.** Item #1 widened `_guard_binary_content_type`
(`src/veniceresch/_client.py:75-124`) to raise `VeniceUnexpectedContentTypeError`
for *any* textual 2xx body on a binary request — `application/json` (line 97) and
now every `text/*` / `application/xml` / `application/xhtml+xml` type
(`_is_textual_content_type`, `:63-72`; raise at `:113-124`). To carve out the one
endpoint that legitimately returns text, an `allowed_content_types` allow-list was
threaded through the guard (`:77`, matched at `:95-96`) and both `_request_bytes`
overloads. The **only** non-empty caller is `augment.parse_text`
(`augment.py:101` async / `:168` sync), which passes `("text/plain",)`.

**Problem A — `video.download()` of a presigned/CDN URL.** `download()` and
`retrieve_binary()` call `_request_bytes` with **no** `allowed_content_types`
(default `()`), so every textual content-type raises. A presigned-URL CDN or
S3-style object store that serves genuine MP4/PNG bytes but labels them
`text/plain` (object stores commonly default to this when no Content-Type
metadata is set) now fails — the user can't download a completed video even
though the bytes are real media. The guard's own docstring (`:81-87`) frames
textual bodies as "CDN error page / presigned-URL error," but a correctly-served
mislabeled object is the false-positive case it doesn't distinguish.

**Problem B — `augment.parse_text` narrowed to `text/plain` only.** Pre-0.6.0
the guard let any non-JSON 2xx body through; now `parse_text` raises for any
textual type other than `text/plain`. If Venice returns extracted document text
as `text/markdown`, `text/html`, or `text/xml` (all plausible for a
text-extraction endpoint), `parse_text` raises instead of returning the string —
breaking previously-working document parsing.

**Problem C — altitude (0.6.0 #8).** `allowed_content_types` widens shared client
infrastructure (`_guard_binary_content_type` + both `_request_bytes` overloads at
`:279`/`:491`, forwarded `:292`/`:504`) for exactly one consumer. The deeper rule
the special case gestures at — "a content-type the request explicitly asked for
via `Accept` is not unexpected" — is never captured, so the next text-returning
binary caller will bolt on another literal tuple.

**Fix (preferred, captures the real rule).** Have the guard honor the request's
`Accept` header: a 2xx body whose content-type matches what the caller asked for
is by definition *not* unexpected and must pass through, textual or not. Then:
- `augment.parse_text` already sends `headers={"Accept": "text/plain"}` (verify),
  so it passes the guard with **no** `allowed_content_types` argument — delete the
  parameter from the guard and both `_request_bytes` overloads (closes #8).
- `video.download()` of a presigned URL sends `Accept: application/octet-stream`
  (or `video/mp4`); a CDN that honors it returns matching bytes and passes. A CDN
  that ignores `Accept` and returns `text/html` (a real error page) still raises —
  the genuine corruption case is preserved.

Keep the `application/json` VPS-video branch (`:97-112`) as-is — that's a
different, documented signal (media lives at `download_url`).

**Fix (minimal fallback, if Accept-matching proves leaky).** Keep
`allowed_content_types` but: (a) default `video.download()`'s presigned-URL path
to a permissive raw-bytes fetch that skips the textual guard entirely (a
presigned URL is an opaque download, not a Venice API surface), and (b) widen
`augment.parse_text`'s allow-list to the textual types a parser realistically
returns (`text/plain`, `text/markdown`, `text/html`, `application/xml`). This
leaves the special case in place — prefer the Accept-header approach.

**Decision needed (carry into the session).** Confirm against Venice's live API
whether `video.download` presigned URLs and `augment.parse_text` actually return
non-`octet-stream`/`text-plain` content-types before choosing how permissive to
be — the integration smoke workflow (item #4) is the place to check. Don't loosen
the guard further than the evidence warrants; over-correcting reopens item #1's
silent-corruption hole.

**Tests** (`tests/`, respx-mocked, async + sync):
- `video.download` with a presigned-URL body labeled `text/plain` but carrying
  real bytes returns the bytes (does not raise).
- `augment.parse_text` returns the string for a `text/markdown` (and `text/html`)
  body.
- A binary endpoint that did **not** ask for a textual type still raises
  `VeniceUnexpectedContentTypeError` on a `text/html` error page (item #1's
  guarantee intact).
- The existing JSON-guard test and the `text/plain` parse_text test keep passing.

**Acceptance:** real-but-mislabeled media downloads succeed; `parse_text` returns
non-`text/plain` textual bodies; genuine error pages on binary endpoints still
fail loudly; if the Accept-header route is taken, `allowed_content_types` is gone
from the client surface.

---

## 10. Make `wait_for_completion`'s terminal check case-insensitive  (0.6.0 #3)  — DONE

**Done (2026-06-29).** Added a module-level `_is_processing(status)` predicate to
both `video.py` and `audio.py` (next to `_FAILURE_STATUSES`): case-insensitive
`status.upper() == _STATUS_PROCESSING`, guarded by `isinstance(status, str)`.
Replaced the exact-match `result.status != _STATUS_PROCESSING` at all four sites
(`video.py` async/sync, `audio.py` async/sync) with `not _is_processing(...)`.
Only the *in-progress* comparison became case-insensitive — the set of statuses
treated as terminal is unchanged ("anything not processing"), so the deliberate
"tolerate unknown terminal statuses" contract from item #3 is preserved, and a
non-string/None status still falls through to terminal exactly as before. The
predicate is the shared casing helper item #12 proposes folding into
`_uploads.py`/`_polling.py`; for now it lives once per module. Added tests: a
lowercase/`Processing` in-progress status keeps the loop polling until
`COMPLETED` (audio async; video async + sync). Existing uppercase, failure,
unknown-terminal, and timeout tests unchanged. 274 tests pass; ruff + mypy clean.

**Priority: high, tiny.** Two-line defensive fix; internal inconsistency
introduced alongside item #3's failure-raising.

**Problem.** The terminal-state check is exact-match uppercase while the failure
check immediately below it is case-insensitive — same method, two different
casing assumptions:

```python
# video.py:258 (async) / :390 (sync); audio.py:236 (async) / :376 (sync)
if result.status != _STATUS_PROCESSING:          # exact-match "PROCESSING"
    if (raise_on_failed and isinstance(result.status, str)
            and result.status.upper() in _FAILURE_STATUSES):   # case-INsensitive
        raise VeniceVideoFailedError(...)
    return result
```

If Venice ever returns the in-progress status as `"processing"` / `"Processing"`,
the `!=` treats it as terminal and `wait_for_completion` returns mid-job; the
caller then calls `download()` / `retrieve_binary()` on an unfinished asset and
gets a `VeniceUnexpectedContentTypeError` (JSON status body, post-item-#1) or
empty media. The `.upper()` on the very next line is the tell that the casing
isn't trusted.

**Constraint.** Item #3 deliberately preserved "return on any non-PROCESSING
status (including unknown ones)." Keep that — only the *PROCESSING comparison*
should become case-insensitive, not the set of statuses treated as terminal.

**Fix.** Compare case-insensitively against `_STATUS_PROCESSING`, e.g.
`isinstance(result.status, str) and result.status.upper() == _STATUS_PROCESSING`
(or normalize once into a local). Apply to all four sites: `video.py:258`/`:390`,
`audio.py:236`/`:376`. Consider a tiny shared `_is_processing(status)` predicate
(see item #12, which already proposes sharing this neighborhood).

**Tests:** a `"processing"` (lowercase) retrieve response keeps the loop polling
(does not return early); existing uppercase `PROCESSING` path unchanged; failure
and timeout paths unchanged. Audio + video, async + sync.

**Acceptance:** a non-uppercase in-progress status no longer ends the wait;
default and `raise_on_failed=True` behavior otherwise unchanged.

---

## 11. Harden the SSE parser's `[DONE]`-in-block and multi-payload edges  (0.6.0 #4)  — DONE

**Done (2026-06-29).** Resolved both sub-cases by documentation + pinning tests,
per the item's own "don't over-engineer / don't restructure speculatively"
guidance — no control-flow change. Problem A: added a comment at the `[DONE]`
branch in `_parse_event` (`_sse.py`) stating that a content payload accumulated
earlier in the *same* event block is intentionally dropped, why that can't happen
on Venice's wire (the module docstring documents `[DONE]` arriving in its own
block, one `data:` line per block), and exactly what to change (decode + yield the
accumulated `payloads` before stopping) if Venice ever co-locates. Problem B:
added a comment at the `json.loads` join noting the join-and-decode-once is
spec-correct (multi-line `data:` is ONE logical payload) and that a non-spec block
carrying two *complete independent* JSON objects raises `JSONDecodeError` out of
the iterator — deliberate, matching the existing "malformed input surfaces"
contract (`test_invalid_json_raises_cleanly`) rather than silently dropping. Added
two tests pinning these decisions (`test_content_payload_colocated_with_done_is_dropped`,
`test_multiple_independent_json_objects_in_one_block_raise_cleanly`), async + sync.
Existing multi-line-join, `[DONE]`-stops, and invalid-JSON tests unchanged. 276
tests pass; ruff + mypy clean. Comments + additive tests only, no production
behavior change, so no CHANGELOG entry (same as items #4, #6, #7, #8).

**Priority: low.** Spec-corner cases that are unlikely against Venice's actual
wire format (single `data:` per event, `[DONE]` in its own block — see
`_sse.py:1-13` docstring). Item #2's multi-`data:` join is otherwise correct.
Flagged for completeness; a comment may be the right resolution for some sub-cases.

**Problem A — payload dropped when sharing a block with `[DONE]`.** `_parse_event`
(`src/veniceresch/resources/_sse.py:50-64`) accumulates `data:` payloads and
`raise _StreamDone` the instant it sees `[DONE]` (`:59-60`). Any content payload
appended earlier in the *same* event block is discarded, and callers
(`aiter_sse_events:78-83` / `iter_sse_events:100-106`) `return` on `_StreamDone`.
If Venice ever packs a final content chunk and `[DONE]` into one block, that chunk
is silently lost (the iterator ends one chunk short). Pinned today by
`test_done_as_second_data_line_still_stops`.

**Problem B — multiple independent JSON payloads in one block.** `:64` joins all
`data:` payloads with `\n` and `json.loads` once — correct per SSE spec (multi-line
`data:` is one logical payload). But if a non-spec server emits two *complete
independent* JSON objects as separate `data:` lines in one block, the joined
`{...}\n{...}` is invalid JSON and `json.loads` raises `JSONDecodeError` out of the
generator, aborting the whole stream. The pre-0.6.0 "return first line" tolerated
this by accident.

**Fix (decide per sub-case; do not over-engineer).**
- A: if Venice's wire format ever co-locates content with `[DONE]`, yield the
  accumulated payload *before* honoring the stop. Otherwise add a code comment at
  `:59-60` documenting that a same-block payload is intentionally dropped and why
  it can't happen with Venice today. Don't restructure the control flow
  speculatively.
- B: wrap the `json.loads` at `:64` so a decode failure on a multi-payload block
  is handled deliberately (skip-and-continue, or split-and-yield-each) instead of
  killing the stream — only if we decide non-spec multi-object blocks are worth
  tolerating. If not, leave as-is (spec-correct) and note it.

Apply to the single `_parse_event` helper — both async and sync iterators call it.

**Tests** (`tests/`, grep `aiter_sse_events`): whichever sub-cases are chosen —
content + `[DONE]` in one block (drop documented or payload preserved); a
malformed multi-object block doesn't abort the surrounding stream. Existing
multi-line-join and `[DONE]`-stops tests keep passing.

**Acceptance:** Venice's current single-`data:` streams are byte-for-byte
unchanged; the chosen edge behaviors are either fixed or explicitly documented as
deliberate.

---

## 12. Share the audio/video job-failure machinery  (0.6.0 #5)  — DONE

**Done (2026-06-29).** Lifted the shared pieces into a new
`src/veniceresch/resources/_polling.py` (chosen over folding into `_uploads.py`,
which stays upload-scoped — mixing job-status logic into an uploads module would
hurt the readability CLAUDE.md prizes; the item explicitly allows the sibling
module). It now holds the single `_FAILURE_STATUSES` frozenset, the
`is_processing` / `is_failure_status` case-insensitive predicates (folding in
item #10's per-module `_is_processing` helper), and a `VeniceJobFailedError`
base carrying `queue_id` / `status` / `result`. `VeniceAudioFailedError` /
`VeniceVideoFailedError` collapse onto thin subclasses that pass a `kind=`
label; their public names, `__init__` signatures, attributes, and the
`__init__.py` re-exports are unchanged. `VeniceJobFailedError` is additionally
re-exported from `__init__.py` so callers can catch both with one `except`. The
four `wait_for_completion` bodies (audio/video, async/sync) now call the shared
predicates. Added `tests/test_polling.py`: a parametrized parity test driving
both resources off the *single* shared set (so a future status addition
exercises both automatically), a hierarchy/identity check, and predicate
case-insensitivity. Did **not** merge the audio/video resources or touch the
sync/async mirroring. 282 tests pass; ruff + mypy clean. New public export, so a
CHANGELOG "Added" entry was added (unlike items #4/#6/#7/#8/#11).

**Priority: medium, cleanup (CONFIRMED duplication).** Item #3 created this
machinery in two places; item #5 of the new release created `_uploads.py` as the
shared-helper home for exactly these mirrored resources, so this is the natural
landing spot.

**Problem.** `_FAILURE_STATUSES = frozenset({"FAILED", "CANCELLED", "CANCELED",
"ERROR"})` is defined identically at `audio.py:39` and `video.py:52`; the
detection branch (`isinstance(result.status, str) and result.status.upper() in
_FAILURE_STATUSES`) is pasted verbatim into all four `wait_for_completion` bodies
(`audio.py:240`/`:380`, `video.py:262`/`:394` — line numbers approximate, confirm
in tree); and `VeniceAudioFailedError` / `VeniceVideoFailedError`
(`audio.py:~62` / `video.py:68`) are structurally identical (same `__init__`
signature, `status_code=0`, `error_body={"queue_id":…, "status":…}` dict, same
three attrs). Risk: when Venice ships a new terminal failure string (e.g.
`"REJECTED"` / `"TIMEOUT"`), an editor updates one frozenset and forgets the
other, so `raise_on_failed=True` diverges between two resources CLAUDE.md
explicitly documents as mirroring each other.

**Fix.** Lift the shared pieces into one place — `_uploads.py` exists for exactly
this (or a sibling `_polling.py` if `_uploads.py` should stay upload-scoped;
prefer reusing `_uploads.py` per the release's own consolidation intent):
- a single `_FAILURE_STATUSES` frozenset;
- a small predicate, e.g. `is_failure_status(status) -> bool` (and, folding in
  item #10, `is_processing(status)`), so casing logic lives once;
- a shared base for the failed errors (e.g. `VeniceJobFailedError(VeniceAPIError)`
  carrying `queue_id` / `status` / `result`), with `VeniceAudioFailedError` /
  `VeniceVideoFailedError` as thin subclasses to keep the existing public names
  and `__init__.py` re-exports stable.

Keep the two named exception classes (callers/`__all__`/`__init__.py` re-export
them) — only their bodies collapse onto the base. Apply across audio + video,
async + sync.

**Constraint.** Don't merge audio and video resources or erase the deliberate
sync/async mirroring (CLAUDE.md: "Two distinct layers; they must stay distinct").
This is shared *constants + predicate + error base*, not a resource refactor.

**Tests:** existing `raise_on_failed` tests for both audio and video still pass
unchanged; add one asserting both resources raise on the *same* status string so
future divergence is caught (parity in spirit of item #6). mypy + ruff clean.

**Acceptance:** failure-status set and predicate defined once; both resources
raise the same typed-error hierarchy; public class names and re-exports unchanged.

---

## 13. Offload blocking file reads off the async event loop on upload/encode paths  (0.6.0 #6, #7)  — DONE

**Done (2026-06-29).** Took the preferred `asyncio.to_thread` read-to-bytes
approach on the async surfaces only; sync paths and `bytes` inputs (already in
memory) are untouched. Added `async_open_upload` to `resources/_uploads.py` — an
`@asynccontextmanager` mirroring `open_upload`'s call shape that reads a path /
caller-supplied handle in a worker thread and hands httpx the resulting `bytes`
(giving up streaming on async, per the item's stated tradeoff, to keep the loop
free); a caller handle is read but never closed. The two async audio methods
(`create_cloned_voice`, `transcribe`) and the two async augment methods
(`parse`, `parse_text`) now `async with async_open_upload(...)`. For images,
added `_encode_image_async` (str passthrough, `bytes` encoded inline = nothing to
offload, Path/file-like read+base64 via `to_thread`) and awaited it in the four
async image methods (`edit`, `multi_edit`, `upscale`, `background_remove`).
Updated the `_uploads.py` and `image.py` module docstrings to note the async read
is offloaded and the streaming tradeoff. Tests: added six `async_open_upload`
unit tests (`test_uploads.py`) mirroring the sync ones (bytes passthrough, path /
str-path / file-like read-to-bytes, missing-path `FileNotFoundError`, caller
handle not closed) and a path-input wire-parity test (`test_sync_async_parity.py`)
proving the async read-to-bytes route and the sync handle-stream route produce a
byte-identical multipart body. Existing image async path/file-like tests
(`test_edit_reads_from_path`, `test_edit_reads_from_file_like`) confirm the encode
offload produces identical base64. 289 tests pass; ruff + mypy clean. CHANGELOG
"Fixed" entry added (real async behavioral fix, though wire output is unchanged).

**Priority: medium, efficiency (CONFIRMED).** Introduced by item #5's
file-like/streaming upload support: the streaming handle keeps disk I/O on the
loop for the whole request rather than buffering once up front.

**Problem A — multipart uploads stream a synchronous handle (0.6.0 #6).**
`open_upload` (`_uploads.py:47-50`) opens a path with a blocking `path.open("rb")`
handle and yields it into `await _client._request_json(files=...)` /
`_request_bytes(files=...)`. httpx's async multipart encoder iterates that handle
with synchronous `file.read()` calls *inside the coroutine*, so uploading a large
file to `/audio/transcriptions`, `/audio/voices`, or `/augment/text-parser`
(`audio.py:~129`, `augment.py:~148`) blocks the event loop for the whole request
write — every other concurrent coroutine stalls. (Pre-0.6.0 `read_bytes()` blocked
once before the request; the streamed handle blocks across it.)

**Problem B — file-like image input read+base64 on the async path (0.6.0 #7).**
`_encode_image` (`image.py:34-47`) does a synchronous `image.read()` (line 47) and
`Path.read_bytes()` (line 44) inside the async coroutines that call it (edit
`~:100`, multi_edit `~:122`, upscale `~:141`, background_remove `~:163`), fully
buffering the file plus its ~33%-larger base64 copy and blocking the loop during
the read.

**Fix.**
- Async paths only: offload the blocking read with `asyncio.to_thread(...)` so
  disk I/O leaves the event loop. For multipart (A), either read the path in a
  thread and hand httpx the resulting `bytes` (simplest; gives up streaming but
  unblocks the loop), or feed httpx an async-friendly file wrapper if one is
  readily available — prefer the `to_thread` read unless streaming large files is
  a stated goal. For image base64 (B), wrap the `read()`/`read_bytes()` +
  `b64encode` in `asyncio.to_thread`.
- Sync paths: unchanged (blocking is correct there).
- Base64-in-JSON inherently buffers — don't try to stream image-generate; the
  fix is purely "don't block the loop on the read." The `image.py:8-10` /
  `_uploads.py` docstrings already document the buffering; extend them to note the
  async read is offloaded.

Keep `bytes` inputs zero-copy (already in memory; nothing to offload) and keep
caller-supplied-handle lifecycle semantics (`_uploads.py:52-56` — never close a
handle we didn't open).

**Tests:** existing upload/image tests (Path / str / bytes / file-handle
parametrization from item #5) still pass and produce identical multipart bodies;
add a check that the async path doesn't regress behavior. (Event-loop-blocking is
hard to assert directly; focus tests on output parity and rely on review for the
`to_thread` offload.)

**Acceptance:** large async uploads / image encodes no longer block the loop for
the duration of the read; sync behavior unchanged; wire output byte-identical to
today.

---

## Secondary observations (no action / framing only)  — ADDRESSED (README pass, 2026-06-29)

**Done (2026-06-29).** Docs-only README framing pass; no code change, no
CHANGELOG entry. Added a "What 'typed' means here" subsection under "Why this
exists" stating the honest contract — typed resource methods + shallow typed
wrappers, nested collections deliberately `dict[str, Any]` for drift tolerance,
`.model_extra` for unknowns, `model_validate(element)` as the strict escape
hatch, framed as an alpha-stage choice (don't oversell deep nested type
safety). Made `client.responses`'s own-API status explicit ("its **own** Venice
API, not an OpenAI-compatibility alias for chat"). The other alias boundaries
(`client.image` vs `client.images`, `chat.create` == `chat.completions.create`)
were already explicit, so left unchanged.

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
