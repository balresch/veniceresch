# venice-sdk

A typed, async-first Python client for the [Venice.ai](https://venice.ai) API.

Built to replace the abandoned community package `venice-ai`
(`github.com/sethbang/venice-ai`, last release 2025-06-25), which doesn't
cover `/image/edit`, `/image/multi-edit`, `/video/queue`, `/video/retrieve`,
and whose `ModelType` literal excludes `"video"`.

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
pip install venice-sdk
```

## Quickstart

```python
import asyncio
from venice_sdk import AsyncVeniceClient

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

## Image: generate, edit, multi-edit

```python
# JSON response (base64-encoded images in the dict)
result = await client.image.generate(model="flux-dev", prompt="a red cube", width=1024, height=1024)

# Raw bytes (PNG/JPEG/WebP)
png_bytes = await client.image.generate_binary(model="flux-dev", prompt="a red cube")

# Edit — accepts bytes, Path, base64 string, or URL
edited = await client.image.edit(image=Path("cat.png"), prompt="make it blue", model="flux-edit")

# Multi-edit (up to 3 images) — missing from the community SDK
combined = await client.image.multi_edit(
    images=[img1_bytes, img2_bytes],
    prompt="merge them",
    model_id="flux-multi-edit",
)

# Upscale / background-remove — also missing from the community SDK
upscaled = await client.image.upscale(image=source_png, scale=2.0)
cutout = await client.image.background_remove(image_url="https://x/pic.png")
```

## Video: queue + poll

```python
queued = await client.video.queue(model="video-v1", prompt="a cat", duration="5s")

# Poll until done (raises VeniceVideoTimeoutError at timeout):
result = await client.video.wait_for_completion(
    model="video-v1", queue_id=queued["queue_id"], timeout_s=600, poll_interval_s=2.0,
)

# Fetch the MP4 bytes:
mp4 = await client.video.retrieve_binary(model="video-v1", queue_id=queued["queue_id"])
```

## Audio: TTS, transcription, queued generation

```python
mp3_bytes = await client.audio.create_speech(input="Hello world", voice="nova")
transcript = await client.audio.transcribe(file=Path("clip.wav"), model="whisper-1")
```

## Models / embeddings / billing

```python
models = await client.models.list(type="video")      # "video" works — unlike the old SDK
emb = await client.embeddings.create(input="hello", model="embed-v1")
balance = await client.billing.balance()
```

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
from venice_sdk import (
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
from venice_sdk import VeniceClient

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
`datamodel-code-generator`, writes `src/venice_sdk/_generated.py`). Pass
`--offline` to use the pinned `vendor/venice-swagger.yaml` instead.

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy src/venice_sdk
pytest                                    # unit tests (offline, respx-mocked)
VENICE_API_KEY=... pytest tests/integration -m integration  # smoke
```

## Endpoint coverage (v0.1.0)

| Group | Covered | Gap |
|---|---|---|
| chat | `/chat/completions`, `/responses` | — |
| image | `/image/generate`, `/image/edit`, `/image/multi-edit`, `/image/upscale`, `/image/background-remove`, `/image/styles` | `/images/generations` (OpenAI alias — use `/image/generate`) |
| video | `/video/queue`, `/video/retrieve`, `/video/quote`, `/video/complete`, `/video/transcriptions` | — |
| audio | `/audio/speech`, `/audio/transcriptions`, `/audio/queue`, `/audio/retrieve`, `/audio/quote`, `/audio/complete` | — |
| models | `/models`, `/models/traits`, `/models/compatibility_mapping` | — |
| embeddings | `/embeddings` | — |
| billing | `/billing/balance`, `/billing/usage`, `/billing/usage-analytics` | — |
| augment | — | `/augment/scrape`, `/augment/search`, `/augment/text-parser` (planned for v0.2) |
| characters | — | `/characters/*` (planned for v0.2) |
| api_keys / x402 | — | out of scope for v0.1.0 |

Anything not in the table above can still be called directly via the
client's low-level request helpers.

## License

MIT.
