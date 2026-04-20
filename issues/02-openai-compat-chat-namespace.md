**Title:** Alias `client.chat.completions.create` to match the `openai` Python SDK namespace

## Summary

Venice's marketed position is "OpenAI-compatible inference API." The largest prospective user base for this SDK is people migrating from the `openai` Python SDK. Their current code is `client.chat.completions.create(...)` — our SDK uses `client.chat.create(...)`, forcing every migrating user to rewrite every chat call. Adding a `completions` sub-resource with the same methods closes that gap with effectively zero maintenance cost.

## Motivation

Today, migrating from `openai` to `venice-sdk` requires editing every chat call site. For a realistic codebase with hundreds of `client.chat.completions.create(...)` calls, that's a big and error-prone refactor — and it's completely unnecessary, because the underlying HTTP endpoint is literally `/chat/completions`.

Concrete evidence: the primary consumer of this SDK (lewdresch) today has 5+ sites using `client.chat.completions.create(...)` against the community SDK. Under the current design, every one of those requires editing; with the alias, migration becomes a single-line import change.

The same pattern holds for anyone in the wider ecosystem: OpenAI's SDK shape is a de facto API standard for inference APIs, and Venice's own docs say "OpenAI-compatible." An OpenAI-namespace-compatible Python SDK leans into that pitch instead of partially breaking it.

## Proposed solution

Add a `completions` sub-resource that wraps the same underlying calls. Implementation is a thin property:

```python
# src/venice_sdk/resources/chat.py

class _AsyncCompletionsSubResource:
    """OpenAI-compatible alias: client.chat.completions.create(...) == client.chat.create(...)."""

    def __init__(self, chat: "AsyncChatResource") -> None:
        self._chat = chat

    async def create(self, **kwargs: Any) -> Any:
        return await self._chat.create(**kwargs)

    def stream(self, **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
        return self._chat.stream(**kwargs)


class AsyncChatResource:
    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client
        self.completions = _AsyncCompletionsSubResource(self)

    async def create(self, ...) -> ...:
        ...  # unchanged
```

Both forms now work:

```python
# existing — still works
await client.chat.create(model="m", messages=[...])

# OpenAI-compatible — now also works
await client.chat.completions.create(model="m", messages=[...])
```

Repeat for the sync `ChatResource` and `_CompletionsSubResource`.

## Why this is strictly additive

- No existing call site breaks — `chat.create` still exists.
- The sub-resource literally delegates; there's no duplication of logic.
- The type signatures match, so mypy is happy in both forms.
- Zero runtime overhead (one extra attribute lookup).

## Acceptance criteria

- [ ] `client.chat.completions.create(...)` works and returns the same response as `client.chat.create(...)`.
- [ ] `client.chat.completions.stream(...)` works and returns the same iterator as `client.chat.stream(...)`.
- [ ] Same for the sync `VeniceClient`.
- [ ] A new test asserts: same kwargs, same HTTP request sent, same response returned for both forms.
- [ ] README adds an OpenAI migration snippet:
  ```python
  # Before (openai)
  from openai import AsyncOpenAI
  client = AsyncOpenAI()
  
  # After (venice-sdk) — literally the same call shape
  from venice_sdk import AsyncVeniceClient
  client = AsyncVeniceClient()
  await client.chat.completions.create(...)
  ```

## Optional extension: `/responses` namespace

Since this issue is about OpenAI compatibility, also consider moving `create_response` off `chat` and into a top-level `client.responses.create(...)` namespace — that's where OpenAI's SDK puts it. Low cost, same win.

## Estimated scope

~1 hour, including tests and README update.
