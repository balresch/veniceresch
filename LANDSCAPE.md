# Python SDK landscape for Venice.ai

Snapshot taken **2026-11-15** (veniceresch 0.9.0). The purpose is to decide what
veniceresch is *for* next to the other Python SDKs, which gaps are worth
closing, and which strengths to build on. Re-run the commands under
[Refreshing this snapshot](#refreshing-this-snapshot) before relying on numbers
older than a few weeks. Concrete follow-ups live in `BACKLOG.md` (items #20+).

## Who uses veniceresch

There's no hard evidence of external users:

- GitHub: 1 star (the owner's), 0 forks, 0 other watchers, every issue/PR by
  the owner, the dependents page shows 0 repositories / 0 packages, 1 page
  view in 14 days. Code search only finds `szabgab/pydigger-data` (an
  automated PyPI metadata crawler) and `veniceai/builtinvenice`, Venice's
  official "Built with Venice" showcase, which lists veniceresch as a Python
  SDK. That listing is a real discovery channel. Code search can't see
  private repos.
- PyPI (pypistats, ~1,490 downloads total, ~215 last month): 1,076 report no
  Python version / OS, which is typical of scanners and mirrors. Linux +
  Python 3.13 matches this host and lewdresch's CI. The 2026-11-09 spike
  lines up with the 0.7.0 release. Python 3.9 downloads can't be real installs
  (`requires-python >= 3.10`).
- **One plausibly external user:** a macOS machine on Python 3.11 with bursts
  of 14 downloads on 2026-07-10 and 12 on 2026-08-31, plus a few around
  2026-11-09. The owner has no Mac. So treat the package as having outside
  users: breaking changes only with a major bump, deprecations kept until 1.0.

Known internal consumer: lewdresch (production, imports from the host's system
Python; see CLAUDE.md and GH #18).

## The other Python SDKs

Found via the showcase (`veniceai/builtinvenice`, `content/projects/*.yaml`,
96 entries; Python SDKs filtered by tags/description) plus PyPI name probes.
Out of scope: `llm-venice` (a plugin for the `llm` CLI) and `venice_ai` (Home
Assistant integration).

| | **veniceresch** | **venice-py** | **venice-sdk** | **pyvenice** |
|---|---|---|---|---|
| Repo | balresch/veniceresch | sethbang/venice-py | actuallyrizzn/Venice-AI-SDK | TheLustriVA/PyVenice |
| PyPI | `veniceresch` | `venice-py` (old name `venice-ai` now installs it) | `venice-sdk` | `pyvenice` |
| Latest | 0.9.0 (2026-11-15) | 2.11.0 (2026-11-10) | 0.3.3 (2026-10-25, only PyPI release) | 0.3.1 (2025-07-15) |
| Activity, 90 days | 11 commits (squash merges) | 245 commits, one maintainer + dependabot | 2 commits | 0 (stale since 2025-07) |
| GitHub | 1★, 0 forks | 13★, 8 forks | 4★, 1 fork | 1★, 0 forks |
| Downloads, last month | 215 | 772, plus 382 on `venice-ai` | 195 | 52 |
| HTTP stack | httpx | aiohttp | requests | httpx |
| Async / sync | both, natively (httpx) | async; sync runs the async client on a background event-loop thread | sync only | — |
| Python floor | 3.10 | 3.11 | 3.8 | 3.12 |
| Runtime deps | httpx, pydantic, typing-extensions | aiohttp[speedups], idna, pydantic, typing-extensions, plus extras (`cli`, `x402`, `x402-solana`, `redis`, `e2ee-verify`) | requests, tiktoken, psutil, python-dotenv, typing-extensions | httpx, pydantic, python-dateutil, typing-extensions |
| Types | generated from Venice's swagger (`datamodel-code-generator`), unknown fields tolerated | hand-written pydantic models | — | — |
| In the showcase | yes | yes | yes ("Python, alt") | no |

Download counts are mostly noise (see above); use them only as a rough ranking.

### venice-py in detail (the real overlap)

A large, fast-moving project. Beyond the API surface it ships:

- retries **on by default** (`max_attempts=2`) and a rate limiter with an
  optional Redis backend, metrics and Grafana dashboards;
- a CLI (`venice-py ...`) covering chat, image, audio, video, models, account;
- x402 wallet auth and **signing** (EVM and Solana), including one-call
  top-ups (`top_up_with`, `top_up_with_solana`);
- TEE / end-to-end encryption with attestation verification, including full
  client-side TDX verification. It uses endpoints that are **not** in the
  public swagger, so it sits outside veniceresch's "49 of 49 paths";
- model selection by capability/price, cost tracking, reasoning controls;
- convenience helpers: `stream.text_deltas()`, `response.save()`,
  `run_with_tools` tool loops, `client.gather(max_concurrency=N)`, a music
  resource;
- ~90 runnable examples and four Claude Code skills it can install.

Not verified here: how complete or correct its endpoint coverage is, or how it
handles the direct-bytes `retrieve` and response-header cases veniceresch fixed
in 0.8/0.9.

### venice-sdk, pyvenice

- **venice-sdk**: synchronous, requests-based, heavy deps (tiktoken, psutil),
  one PyPI release, little activity, no declared license (`NOASSERTION`).
- **pyvenice**: httpx + pydantic like us, but abandoned since 2025-07.

Neither is meaningful overlap.

## Positioning

For a new user who wants features, venice-py is the default choice and does
far more. veniceresch competing on breadth (CLI, rate limiter, wallet signing,
TEE) would mean chasing a much better-resourced project.

veniceresch's reasons to exist, which are also its strengths to build on:

1. **Spec-generated and drift-guarded.** Types come from Venice's own swagger,
   regeneration is scripted, and positional generated names are guarded by
   tests (`tests/test_model_types.py`). This makes it fast to follow spec
   changes (the 20261108 sync) and makes "covers the documented API" checkable.
2. **Thin and predictable.** Three runtime deps, no hidden retries or
   background threads, a native sync client, typed errors you dispatch on
   yourself. Easy to embed in a service that already has its own retry,
   logging and concurrency policy (lewdresch).
3. **Wire correctness, verified live.** Typed errors for non-JSON bodies,
   dual-shape `retrieve`, image header metadata confirmed against the real
   API, a live integration suite (free / paid / admin tiers).
4. **Python 3.10 floor.**

## Decisions (2026-11-15)

- **Don't compete on breadth.** No CLI, no built-in retries or rate limiter,
  no bundled wallet signer, no TEE/E2EE for now. These stay out unless a
  concrete consumer needs them.
- **Close obvious gaps where it's cheap**, in ways that fit the thin design:
  helpers for caller-owned retries rather than retrying for them, a streaming
  text helper, a save helper, runnable examples.
- **Build on the strengths:** automatic spec-drift detection, a test that ties
  every spec path to a resource method, response metadata beyond images
  (`X-Balance-Remaining` is declared on 26 operations; only images surface it).
- **Say what we're for** in the README and the showcase entry, so the overlap
  with venice-py is a stated choice.
- **BACKLOG #18 (wallet auth on all 29 `siwx` routes) is deprioritized:**
  venice-py already covers wallet auth including signing, and anyone who needs
  x402 will likely use it.

See `BACKLOG.md` items #20 onward for the work these decisions produced.

## Refreshing this snapshot

```bash
# Python SDKs in Venice's showcase
gh api "repos/veniceai/builtinvenice/git/trees/main?recursive=1" \
  --jq '.tree[] | select(.path|startswith("content/projects/")) | .path'
# then read the YAML files and filter tags/description for sdk/python

# PyPI names worth probing
for n in venice-py venice-ai venice-sdk pyvenice veniceresch; do
  curl -s "https://pypi.org/pypi/$n/json" | python3 -c \
    "import json,sys; i=json.load(sys.stdin)['info']; print('$n', i['version'], i['summary'])"
done

# Downloads (pypistats rate-limits bursts: space requests ~10s apart)
curl -s https://pypistats.org/api/packages/<pkg>/recent
curl -s https://pypistats.org/api/packages/veniceresch/system        # OS breakdown
curl -s https://pypistats.org/api/packages/veniceresch/python_minor  # Python versions

# GitHub signals for our repo (traffic needs push access)
gh api repos/balresch/veniceresch/traffic/views
gh api repos/balresch/veniceresch/traffic/clones
gh search code veniceresch --json repository --jq '[.[].repository.nameWithOwner] | unique'
curl -s https://github.com/balresch/veniceresch/network/dependents | grep -oE '[0-9,]+ +(Repositories|Packages)'

# Competitor activity
gh api repos/<owner>/<repo> --jq '{stars: .stargazers_count, forks: .forks_count, pushed: .pushed_at}'
gh api "repos/<owner>/<repo>/commits?since=<ISO date>&per_page=100" --jq length   # paginate past 100
```
