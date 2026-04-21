# veniceresch

A typed, async-first Python client for the [Venice.ai](https://venice.ai) API.

## Why this exists

- **Venice has no official Python SDK.** `github.com/veniceai` publishes a
  CLI, docs, MCP server, and x402 client — no Python library.
- **But they do publish an OpenAPI 3.0 spec** at
  `github.com/veniceai/api-docs/blob/main/swagger.yaml`.
- This project treats that spec as the source of truth for types and wraps
  it in a small hand-written `httpx` client with Venice-specific ergonomics
  (`venice_parameters`, typed errors, binary response handling, video
  polling helper).

## Install

```bash
pip install veniceresch
```

## Quickstart

```python
import asyncio
from veniceresch import AsyncVeniceClient

async def main():
    async with AsyncVeniceClient(api_key="...") as client:   # or set VENICE_API_KEY
        response = await client.chat.create(
            model="llama-3.3-70b",
            messages=[{"role": "user", "content": "Hello!"}],
            venice_parameters={"include_venice_system_prompt": False},
        )
        print(response.choices[0]["message"]["content"])

asyncio.run(main())
```

The OpenAI-namespaced form works too — same call, identical HTTP:

```python
await client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

The most common OpenAI-compatible fields (`temperature`, `top_p`, `n`,
`stop`, `max_tokens`, `frequency_penalty`, `presence_penalty`, `seed`,
`tools`, `tool_choice`, `response_format`, `logprobs`) are named
parameters so your IDE can autocomplete them. Everything else Venice
accepts (`min_p`, `repetition_penalty`, `reasoning_effort`,
`prompt_cache_key`, `top_k`, …) still flows through as `**extra` and is
forwarded verbatim:

```python
await client.chat.create(
    model="llama-3.3-70b",
    messages=[{"role": "user", "content": "Summarize today's news."}],
    temperature=0.5,
    max_tokens=512,
    response_format={"type": "json_object"},
    tools=[{"type": "function", "function": {"name": "get_time"}}],
    tool_choice="auto",
    # Venice-specific extras still accepted via **extra:
    min_p=0.05,
    reasoning_effort="medium",
)
```

## Streaming

Pass ``stream=True`` to get an async iterator. **``await`` the call, then
``async for`` the iterator** (same contract as the ``openai`` SDK):

```python
stream = await client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[{"role": "user", "content": "Tell me a story."}],
    stream=True,
)
async for event in stream:
    delta = event.choices[0]["delta"].get("content", "")
    print(delta, end="", flush=True)
```

`client.chat.stream(...)` is an explicit alias; it uses the same
await-then-iterate contract.

`/responses` streams through the same contract:

```python
stream = await client.responses.create(
    model="venice-reasoning-1",
    input="Tell me a short joke.",
    stream=True,
)
async for event in stream:
    # Venice's per-chunk schema isn't in their swagger yet; known
    # identifier fields (id/object/created_at/model) are typed, and
    # everything else (deltas, block events, sequence numbers, …)
    # lands on event.model_extra.
    print(event.model_extra)
```

`client.responses.stream(...)` is the explicit alias.

## Image: generate, edit, multi-edit

```python
# JSON response (base64-encoded images in the dict)
result = await client.image.generate(model="flux-dev", prompt="a red cube", width=1024, height=1024)

# Raw bytes (PNG/JPEG/WebP)
png_bytes = await client.image.generate_binary(model="flux-dev", prompt="a red cube")

# Edit — accepts bytes, Path, base64 string, or URL
edited = await client.image.edit(image=Path("cat.png"), prompt="make it blue", model="flux-edit")

# Multi-edit (up to 3 images)
combined = await client.image.multi_edit(
    images=[img1_bytes, img2_bytes],
    prompt="merge them",
    model_id="flux-multi-edit",
)

# Upscale / background-remove
upscaled = await client.image.upscale(image=source_png, scale=2.0)
cutout = await client.image.background_remove(image_url="https://x/pic.png")
```

### OpenAI-compatible image alias

Drop-in replacement for `openai.images.generate(...)`. Hits Venice's
separate `/images/generations` endpoint, which accepts the full OpenAI
parameter set (many are accepted for compatibility but not used by
Venice — see the endpoint's swagger for the list). `n` is clamped to 1.

```python
result = await client.images.generate(
    prompt="a red cube",
    n=1,
    size="1024x1024",
    response_format="b64_json",
)
print(result.data[0]["b64_json"])
```

`client.image` (singular) is the primary Venice-native image surface and
covers more endpoints (edit, multi-edit, upscale, background-remove,
styles). `client.images` (plural) exists only for OpenAI compatibility.

## Video: queue + poll

```python
queued = await client.video.queue(model="video-v1", prompt="a cat", duration="5s")

# Poll until done (raises VeniceVideoTimeoutError at timeout):
result = await client.video.wait_for_completion(
    model="video-v1", queue_id=queued.queue_id, timeout_s=600, poll_interval_s=2.0,
)
print(result.status)  # "COMPLETED"

# Fetch the MP4 bytes:
mp4 = await client.video.retrieve_binary(model="video-v1", queue_id=queued.queue_id)
```

Queue / retrieve / quote / complete / transcribe all return typed
Pydantic models (`VideoQueueResponse`, `VideoRetrieveResponse`, etc.).
Attribute access everywhere — ``queued.queue_id`` and
``result.status``, not dict indexing.

## Audio: TTS, transcription, queued generation

```python
mp3_bytes = await client.audio.create_speech(input="Hello world", voice="nova")
transcript = await client.audio.transcribe(file=Path("clip.wav"), model="whisper-1")
print(transcript.text)
```

Queued audio generation mirrors video — `client.audio.queue(...)` →
`AudioQueueResponse`, poll `client.audio.retrieve(...)` /
`wait_for_completion(...)` → `AudioRetrieveResponse`, then
`retrieve_binary(...)` for the audio bytes.

## Models / embeddings / billing

```python
models = await client.models.list(type="video")
emb = await client.embeddings.create(input="hello", model="embed-v1")
balance = await client.billing.balance()
```

## Augment: scrape, search, parse

```python
scraped = await client.augment.scrape(url="https://example.com")
results = await client.augment.search(query="venice ai", limit=5)

# Parse a PDF/DOCX/XLSX/text file — JSON form returns {text, tokens}
parsed = await client.augment.parse(file=Path("doc.pdf"))
print(parsed.text, parsed.tokens)

# Plain-text form returns a str directly (Accept: text/plain)
raw_text = await client.augment.parse_text(file=Path("doc.pdf"))
```

## Characters

```python
listing = await client.characters.list(sort_by="featured", limit=20)
for item in listing.data:
    print(item["slug"], item["name"])

character = await client.characters.get("lucy")
reviews = await client.characters.reviews("lucy", page=1, page_size=20)
print(reviews.summary, reviews.pagination)
```

Query parameters use Python snake_case (`is_adult`, `is_pro`,
`is_web_enabled`, `sort_by`, `sort_order`, `model_id`, `page_size`); the
client translates them to the camelCase Venice expects.

## Error handling

Every failure raises a subclass of `VeniceError`. HTTP responses map to
`VeniceAPIError`; transport-level failures (DNS, TLS, timeouts) map to
`VeniceConnectionError` / `VeniceTimeoutError`:

| Exception | When |
|---|---|
| `VeniceAuthError` | 401 — bad or missing API key |
| `VeniceInsufficientBalanceError` | 402 — balance exhausted |
| `VeniceValidationError` | 400 / 422 — bad request shape |
| `VeniceNotFoundError` | 404 |
| `VeniceRateLimitError` | 429 |
| `VeniceServerError` | 5xx |
| `VeniceContentViolationError` | body contained `suggested_prompt` (any status) |
| `VeniceConnectionError` | DNS / TLS / connection reset / proxy failure |
| `VeniceTimeoutError` | request or response timed out |

```python
from veniceresch import (
    VeniceConnectionError,
    VeniceContentViolationError,
    VeniceRateLimitError,
    VeniceServerError,
    VeniceTimeoutError,
)

# Retriable failures — no httpx imports needed:
try:
    await client.chat.create(model="m", messages=[...])
except (VeniceRateLimitError, VeniceServerError,
        VeniceConnectionError, VeniceTimeoutError):
    ...  # back off and retry

try:
    await client.image.generate(model="m", prompt="...")
except VeniceContentViolationError as exc:
    if exc.suggested_prompt:
        retry = await client.image.generate(model="m", prompt=exc.suggested_prompt)
```

`VeniceConnectionError.__cause__` is the underlying `httpx` exception if
you need to introspect it.

## Sync client

```python
from veniceresch import VeniceClient

with VeniceClient(api_key="...") as client:
    for event in client.chat.completions.create(
        model="...", messages=[...], stream=True,
    ):
        ...
```

Sync `stream()` returns an iterator directly (no `await` — that form is
async-only).

## Development

Types come from Venice's upstream OpenAPI spec, regenerated via
`bash scripts/regen_types.sh` (pulls the latest swagger, runs
`datamodel-code-generator`, writes `src/veniceresch/_generated.py`). Pass
`--offline` to use the pinned `vendor/venice-swagger.yaml` instead.

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy src/veniceresch
pytest                                    # unit tests (offline, respx-mocked)
VENICE_API_KEY=... pytest tests/integration -m integration  # smoke
```

## Endpoint coverage

| Group | Covered | Gap |
|---|---|---|
| chat | `/chat/completions` | — |
| responses | `/responses` (streaming + non-streaming) | — |
| image | `/image/generate`, `/image/edit`, `/image/multi-edit`, `/image/upscale`, `/image/background-remove`, `/image/styles`, `/images/generations` (OpenAI alias via `client.images.generate`) | — |
| video | `/video/queue`, `/video/retrieve`, `/video/quote`, `/video/complete`, `/video/transcriptions` | — |
| audio | `/audio/speech`, `/audio/transcriptions`, `/audio/queue`, `/audio/retrieve`, `/audio/quote`, `/audio/complete` | — |
| models | `/models`, `/models/traits`, `/models/compatibility_mapping` | — |
| embeddings | `/embeddings` | — |
| billing | `/billing/balance`, `/billing/usage`, `/billing/usage-analytics` | — |
| augment | `/augment/scrape`, `/augment/search`, `/augment/text-parser` | — |
| characters | `/characters`, `/characters/{slug}`, `/characters/{slug}/reviews` | — |
| api_keys / x402 | — | out of scope |

Anything not in the table above can still be called directly via the
client's low-level request helpers.

Non-goals (unchanged from v0.1): retry/backoff, CLI, SSE parsing beyond
decoded JSON events, tool-use schema builders.

## License

MIT.
