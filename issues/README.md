# venice-sdk proposed issues

Four changes that would improve the SDK as a standalone product **and** simultaneously minimize migration churn for its first real consumer (lewdresch). The common thread: aligning the SDK with how Venice itself markets its API ("OpenAI-compatible") and how its types are actually described in the upstream OpenAPI spec.

File these via `gh issue create --body-file 01-typed-response-models.md ...` etc.

## The four issues

| # | Title | Why it ships | Scope |
|---|---|---|---|
| [01](01-typed-response-models.md) | Return Pydantic models instead of raw dicts | Unblocks "typed SDK" branding; uses the `_generated.py` models that already exist; enables attribute access and mypy on responses | ~1 day |
| [02](02-openai-compat-chat-namespace.md) | Alias `chat.completions.create` for OpenAI compatibility | Drop-in substitution for `openai` Python SDK users; strictly additive | ~1 hour |
| [03](03-stream-true-in-create.md) | Let `create(stream=True)` return an async iterator | Matches OpenAI's streaming idiom; unblocks every streaming tutorial that uses the standard pattern | ~1 hour |
| [04](04-typed-transport-exceptions.md) | Wrap httpx transport exceptions in typed `VeniceError` subclasses | Callers stop having to import `httpx.*` in their except clauses; single error taxonomy | ~2 hours |

## Suggested order

Land them in this order:

1. **#04** first (transport exceptions) — smallest blast radius, improves error handling across every subsequent test you'll write.
2. **#02** next (namespace alias) — pure addition, can ship with zero test rewrites.
3. **#03** (`stream=True` support) — builds on the existing streaming path.
4. **#01** (typed responses) — biggest and best done last; benefits from the cleaner error paths from #04 and the overloaded signatures from #03 (`Literal[True]` → iterator of typed chunks becomes clean).

Together these four land the SDK at v0.2.0 as a genuinely drop-in replacement for `openai`-against-Venice usage, and shrink lewdresch's migration from ~15 mechanical edits + silent-failure fixes to roughly "change the import statement and swap two exception names."
