#!/usr/bin/env python3
"""Compare Venice's upstream OpenAPI spec with the vendored copy (BACKLOG #20).

    .venv/bin/python scripts/spec_drift.py [--upstream URL] [--vendored PATH] [--output FILE]

Prints a Markdown summary of the differences: spec version, added / removed
operations, operations and component schemas whose structure changed, and
those where only descriptions / summaries / examples changed (listed apart,
since upstream edits docs often and that rarely needs a code change).

Exit codes: 0 = no drift, 1 = drift (summary written), 2 = error (e.g. fetch
failed). The weekly ``spec-drift.yml`` workflow turns exit 1 into a GitHub
issue. It never regenerates anything: run ``scripts/regen_types.sh`` yourself.

Only needs PyYAML (in the dev extras) and the standard library.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

import yaml

UPSTREAM = "https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml"
VENDORED = Path(__file__).resolve().parent.parent / "vendor" / "venice-swagger.yaml"
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
DOC_KEYS = {"description", "summary", "example", "examples", "x-codeSamples", "externalDocs"}
LIST_LIMIT = 40


def load_upstream(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "veniceresch-spec-drift"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return yaml.safe_load(resp.read())


def strip_docs(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: strip_docs(v) for k, v in node.items() if k not in DOC_KEYS}
    if isinstance(node, list):
        return [strip_docs(v) for v in node]
    return node


def canon(node: Any) -> str:
    return json.dumps(node, sort_keys=True, default=str)


def operations(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        f"{method.upper()} {path}": op
        for path, ops in (spec.get("paths") or {}).items()
        for method, op in ops.items()
        if method in HTTP_METHODS
    }


def classify(old: dict[str, Any], new: dict[str, Any]) -> dict[str, list[str]]:
    """Split keys into added / removed / changed (structural) / docs-only."""
    out: dict[str, list[str]] = {"added": [], "removed": [], "changed": [], "docs": []}
    out["added"] = sorted(set(new) - set(old))
    out["removed"] = sorted(set(old) - set(new))
    for key in sorted(set(old) & set(new)):
        if canon(old[key]) == canon(new[key]):
            continue
        if canon(strip_docs(old[key])) == canon(strip_docs(new[key])):
            out["docs"].append(key)
        else:
            out["changed"].append(key)
    return out


def bullet_list(items: list[str]) -> list[str]:
    lines = [f"- `{item}`" for item in items[:LIST_LIMIT]]
    if len(items) > LIST_LIMIT:
        lines.append(f"- … and {len(items) - LIST_LIMIT} more")
    return lines


def summarize(old: dict[str, Any], new: dict[str, Any]) -> tuple[bool, str]:
    old_v = (old.get("info") or {}).get("version")
    new_v = (new.get("info") or {}).get("version")
    ops = classify(operations(old), operations(new))
    schemas = classify(
        (old.get("components") or {}).get("schemas") or {},
        (new.get("components") or {}).get("schemas") or {},
    )
    drift = old_v != new_v or any(ops.values()) or any(schemas.values())
    if not drift:
        return False, f"No drift: upstream matches `vendor/venice-swagger.yaml` (spec `{old_v}`).\n"

    lines = [
        "The upstream Venice OpenAPI spec differs from `vendor/venice-swagger.yaml`.",
        "",
        f"- Spec version: vendored `{old_v}` → upstream `{new_v}`",
        f"- Operations: +{len(ops['added'])} / -{len(ops['removed'])} / "
        f"{len(ops['changed'])} changed / {len(ops['docs'])} docs-only",
        f"- Component schemas: +{len(schemas['added'])} / -{len(schemas['removed'])} / "
        f"{len(schemas['changed'])} changed / {len(schemas['docs'])} docs-only",
    ]
    sections = [
        ("New operations", ops["added"]),
        ("Removed operations", ops["removed"]),
        ("Operations with structural changes", ops["changed"]),
        ("New schemas", schemas["added"]),
        ("Removed schemas", schemas["removed"]),
        ("Schemas with structural changes", schemas["changed"]),
        ("Operations with doc-only changes", ops["docs"]),
        ("Schemas with doc-only changes", schemas["docs"]),
    ]
    for title, items in sections:
        if items:
            lines += ["", f"### {title}", "", *bullet_list(items)]
    lines += [
        "",
        "### Next steps",
        "",
        '1. `PATH="$PWD/.venv/bin:$PATH" bash scripts/regen_types.sh` '
        "(updates the vendored spec and `_generated.py`).",
        "2. Wrap new operations; `tests/test_spec_coverage.py` lists what's unmapped.",
        "3. Re-run `tests/test_model_types.py` (positional generated names) and the "
        "live integration smoke.",
        "",
        "_Opened by `.github/workflows/spec-drift.yml` (`scripts/spec_drift.py`)._",
    ]
    return True, "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--upstream", default=UPSTREAM, help="URL of the upstream spec")
    parser.add_argument("--vendored", type=Path, default=VENDORED, help="vendored spec path")
    parser.add_argument("--output", type=Path, help="also write the summary to this file")
    args = parser.parse_args(argv)

    try:
        old = yaml.safe_load(args.vendored.read_text())
        new = load_upstream(args.upstream)
    except Exception as exc:  # network, YAML or file errors
        print(f"spec_drift: could not load specs: {exc}", file=sys.stderr)
        return 2
    drift, text = summarize(old, new)
    print(text, end="")
    if args.output:
        args.output.write_text(text)
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
