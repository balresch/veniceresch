**Title:** Return Pydantic models from resource methods instead of raw dicts

## Summary

Resource methods currently return `dict[str, Any]` even though `src/venice_sdk/_generated.py` already contains Pydantic models generated from Venice's OpenAPI spec. Wire the generated types into the public return values so callers get attribute access, IDE autocomplete, mypy-checked field access, and forward-compat via `extra="allow"`.

## Motivation

The package markets itself as *"typed, async-first Python client."* Today the "typed" part holds for request inputs (explicit kwargs) but not responses — every call returns a plain dict.

Concrete consequences:

- No attribute access: callers write `response["choices"][0]["message"]["content"]` instead of `response.choices[0].message.content`.
- No autocomplete/mypy on field access: typo `response["choces"]` fails at runtime with `KeyError`, not at type-check time.
- The swagger-derived Pydantic models in `_generated.py` sit unused — effectively dead code that the `scripts/regen_types.sh` workflow writes and nobody reads.
- Users porting from the `openai` Python SDK expect pydantic-style response objects; currently they have to invert every access pattern.

The usual counter-argument — "Pydantic validation breaks when Venice adds new fields" — is neutralized by Pydantic v2's `ConfigDict(extra="allow")`: unknown fields are silently stored and don't raise.

## Proposed solution

### 1. Apply `extra="allow"` globally to generated models

In `scripts/regen_types.sh`, pass `--field-extra-keys` and configure the generator to emit `model_config = ConfigDict(extra="allow")` on every class. datamodel-code-generator supports this via:

```
--output-model-type pydantic_v2.BaseModel \
--additional-imports "pydantic.ConfigDict" \
--use-default-kwarg
```

Alternatively, regen as-is and post-process: after generation, inject `model_config = ConfigDict(extra="allow")` into each `class X(BaseModel):`. A few lines of sed in the script is fine.

### 2. Wire the types into resource returns

Change each resource method that currently returns `dict[str, Any]` to parse the response body into the swagger-typed model when the spec has one:

```python
# src/venice_sdk/resources/chat.py
from venice_sdk._generated import ChatCompletionResponse  # or closest matching name

async def create(
    self,
    *,
    model: str,
    messages: Sequence[Mapping[str, Any]],
    venice_parameters: Mapping[str, Any] | None = None,
    **extra: Any,
) -> ChatCompletionResponse:
    ...
    raw = await self._client._request_json("POST", "/chat/completions", json_body=body)
    return ChatCompletionResponse.model_validate(raw)
```

Repeat for `image.generate` → `ImageResponse` (or closest), `models.list` → typed `ModelList`, `billing.balance` → `BillingBalanceResponse`, `embeddings.create` → `CreateEmbeddingResponse`, etc.

Where the swagger does not define a response schema (e.g. `/image/generate`'s `application/json` `$ref` is `None`), keep the `dict[str, Any]` return. Document this per-method.

### 3. Curate `types.py`

Re-export only the types callers should see from `src/venice_sdk/types.py`. Example:

```python
# src/venice_sdk/types.py
from venice_sdk._generated import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelResponse,
    ModelList,
    BillingBalanceResponse,
    # ... curated list; everything not re-exported stays private ...
)

__all__ = ["ChatCompletionRequest", "ChatCompletionResponse", "ModelResponse", ...]
```

### 4. Type the streaming iterator

`chat.stream(...)` yields dicts today. Parse each SSE event into a `ChatCompletionChunk` (or whatever the delta schema is named):

```python
async def stream(
    self, ...
) -> AsyncIterator[ChatCompletionChunk]:
    async with ... as response:
        async for event in aiter_sse_events(response.aiter_bytes()):
            yield ChatCompletionChunk.model_validate(event)
```

### 5. Dict-like access on models (optional, for migration ergonomics)

Pydantic v2 models already support `.model_dump()`; callers who want a dict can opt in. If you want mapping-style `response["choices"]` to keep working (useful for users who copy-paste examples that used OpenAI's raw dicts), add a tiny mixin:

```python
class _DictAccessMixin:
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)
```

Applied to the shared base class of generated models. Not strictly required.

## Acceptance criteria

- [ ] Every resource method whose swagger response has a defined schema returns a typed Pydantic model.
- [ ] All generated Pydantic models have `model_config = ConfigDict(extra="allow")`.
- [ ] `mypy --strict` still passes.
- [ ] A new test verifies that unknown fields in a response body do not raise:
  ```python
  async def test_response_tolerates_unknown_fields(mock_api, async_client):
      mock_api.post("/chat/completions").respond(200, json={
          "id": "x", "choices": [...], "new_field_venice_added_last_week": 42,
      })
      result = await async_client.chat.create(model="m", messages=[{"role": "user", "content": "h"}])
      assert result.id == "x"  # attribute access works
      assert result.choices[0].message.content == "..."  # nested attribute access works
  ```
- [ ] README is updated with examples that use attribute access.
- [ ] `CHANGELOG.md` notes this as a breaking change (bump to 0.2.0).

## Backwards compatibility

Breaking for anyone who wrote `response["choices"][0]` — they'd need `response.choices[0]` (or opt into the optional `__getitem__` mixin). This is the right breaking change to ship now, before a wider user base forms.

## Estimated scope

~1 day. Most of the work is wiring up `_generated` imports into each resource and adjusting tests to assert attribute access. The post-processing step for `extra="allow"` is a short sed/Python pass inside `regen_types.sh`.
