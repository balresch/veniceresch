**Title:** Let `create(stream=True)` return an async iterator, not just require `.stream(...)`

## Summary

Callers coming from OpenAI's Python SDK (and from the abandoned `venice-ai` community SDK) write `create(..., stream=True)` and iterate the result. Today this SDK rejects `stream=True` with a `ValueError` and forces callers to use a separate `.stream(...)` method. Support both forms. Typed return overloads keep mypy honest.

## Motivation

Excerpt from current code:

```python
# src/venice_sdk/resources/chat.py
async def create(
    self, *,
    model: str,
    messages: Sequence[Mapping[str, Any]],
    ...
    **extra: Any,
) -> dict[str, Any]:
    if extra.get("stream"):
        raise ValueError("Pass stream=True via .stream(...), not .create(stream=True).")
    ...
```

The OpenAI SDK's idiomatic streaming shape is:

```python
stream = await client.chat.completions.create(
    model="...", messages=[...], stream=True,
)
async for chunk in stream:
    ...
```

Every internet example using OpenAI's streaming uses this exact pattern. Forcing users to split into a separate method name means:

- Everyone coming from OpenAI has to refactor their streaming call sites.
- Tutorials, LLM-generated examples, and copy-pasted snippets all silently produce `ValueError` until read closely.
- Migrating consumers (lewdresch included) have boilerplate rewrites for no technical benefit.

The underlying implementation already branches on `stream`. Exposing that branch to callers is basically free.

## Proposed solution

### 1. Accept `stream=True` in `create(...)` and return the right shape

Use `@overload` so mypy disambiguates by the literal:

```python
# src/venice_sdk/resources/chat.py
from typing import Literal, overload

class AsyncChatResource:
    @overload
    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[False] = False,
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> ChatCompletionResponse: ...

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: Literal[True],
        venice_parameters: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> AsyncIterator[ChatCompletionChunk]: ...

    async def create(self, *, stream: bool = False, **kwargs: Any) -> Any:
        if stream:
            return self._create_stream(**kwargs)
        return await self._create_non_stream(**kwargs)
```

`.stream(...)` stays as a clean alias — some users will prefer it because the type is narrowed without needing the overload:

```python
async def stream(self, **kwargs: Any) -> AsyncIterator[ChatCompletionChunk]:
    return self._create_stream(**kwargs)
```

### 2. Same treatment for the sync `ChatResource`

Return `Iterator[ChatCompletionChunk]` for `stream=True`, dict/model for `stream=False`.

### 3. Drop the `stream=True` rejection

Remove:

```python
if extra.get("stream"):
    raise ValueError("Pass stream=True via .stream(...), not .create(stream=True).")
```

## Why this plays nicely with typed responses (issue #1)

Once resource methods return typed Pydantic models, the `@overload` signatures get even nicer: `Literal[True]` → `AsyncIterator[ChatCompletionChunk]`, `Literal[False]` → `ChatCompletionResponse`. No `Any` leakage.

## Acceptance criteria

- [ ] `create(stream=True)` returns an async iterator that yields decoded SSE events.
- [ ] `create(stream=False)` and `create()` (default) return the completion as today.
- [ ] `.stream(...)` still works as an alias for `create(stream=True)`.
- [ ] `@overload` signatures are correct: mypy resolves the return type from the `stream` literal without `cast` at call sites.
- [ ] A test asserts both patterns produce the same events from the same mocked SSE body:
  ```python
  async def test_create_stream_true_matches_stream_method(mock_api, async_client):
      body = b"data: {\"a\":1}\n\ndata: [DONE]\n\n"
      mock_api.post("/chat/completions").respond(200, stream=body, headers={"content-type": "text/event-stream"})
      
      via_create = [chunk async for chunk in await async_client.chat.create(
          model="m", messages=[{"role": "user", "content": "h"}], stream=True,
      )]
      # reset mock, make the same call via .stream()
      via_stream = [chunk async for chunk in async_client.chat.stream(
          model="m", messages=[{"role": "user", "content": "h"}],
      )]
      assert via_create == via_stream == [{"a": 1}]
  ```
- [ ] README streaming example uses the OpenAI-idiomatic `stream=True` form.

## Subtle gotcha to watch for

`async def create(..., stream=True)` returns a coroutine that must be `await`ed before iteration — OpenAI's SDK has the same shape:

```python
stream = await client.chat.create(stream=True, ...)  # await returns the iterator
async for chunk in stream:                            # iterate
    ...
```

This is the established convention; documenting it in a README comment is enough.

## Estimated scope

~1 hour, including overloads, tests, and docs.
