#!/usr/bin/env bash
# Regenerate src/veniceresch/_generated.py from Venice's upstream OpenAPI spec.
#
# Usage:
#   bash scripts/regen_types.sh            # fetch fresh swagger, then generate
#   bash scripts/regen_types.sh --offline  # skip fetch; use the pinned vendor copy
set -euo pipefail

SWAGGER_URL="https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml"
VENDORED="vendor/venice-swagger.yaml"
OUT="src/veniceresch/_generated.py"

if [[ "${1:-}" != "--offline" ]]; then
    echo "==> Fetching $SWAGGER_URL"
    curl -fsSL "$SWAGGER_URL" -o "$VENDORED"
else
    echo "==> Using pinned $VENDORED (offline mode)"
fi

echo "==> Generating $OUT"
datamodel-codegen \
    --input "$VENDORED" \
    --input-file-type openapi \
    --output "$OUT" \
    --output-model-type pydantic_v2.BaseModel \
    --base-class veniceresch._base_model.VeniceBaseModel \
    --target-python-version 3.10 \
    --use-annotated \
    --use-double-quotes \
    --use-union-operator \
    --use-standard-collections \
    --field-constraints \
    --collapse-root-models \
    --disable-timestamp \
    --custom-file-header "# AUTO-GENERATED from vendor/venice-swagger.yaml. Do not edit by hand."

echo "==> Stripping per-class extra=\"forbid\" overrides"
# datamodel-codegen emits `model_config = ConfigDict(extra="forbid")` on every
# schema that has `additionalProperties: false` in the swagger, which shadows
# the extra="allow" we set on VeniceBaseModel. We want Venice to be able to
# add fields without breaking clients, so strip those overrides.
#
# NOTE: the strip below is a regex keyed to datamodel-codegen's exact output
# formatting (a multi-line `ConfigDict(\n        extra="forbid",\n    )`). If a
# future generator version reformats that block — single-line, reordered, or
# combined with other ConfigDict options — the regex can silently miss classes
# and leave extra="forbid" in place, which would reintroduce drift-intolerance.
# The post-generation guard below catches exactly that case; if it trips,
# inspect the new ConfigDict formatting and update the regex to match.
python3 - "$OUT" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path).read()
pattern = re.compile(
    r'    model_config = ConfigDict\(\n        extra="forbid",\n    \)\n',
    re.MULTILINE,
)
new = pattern.sub("", text)
open(path, "w").write(new)
print(f"==> Stripped {len(pattern.findall(text))} extra=forbid overrides")
PY

echo "==> Formatting"
ruff format "$OUT"

echo "==> Guarding: no extra=\"forbid\" survived the strip"
# Fail loudly if any extra="forbid" remains. A leftover means the strip regex no
# longer matches the generator's output (see NOTE above) and the regenerated
# types would forbid unknown fields, breaking Venice drift tolerance. Do not
# commit generated types in this state — fix the strip and regenerate.
if grep -n 'forbid' "$OUT"; then
    echo "ERROR: extra=\"forbid\" survived the strip in $OUT (see lines above)." >&2
    echo "       Update the strip regex in scripts/regen_types.sh to match the" >&2
    echo "       current datamodel-codegen output, then regenerate." >&2
    exit 1
fi

echo "==> Done: $OUT"
echo "==> Reminder: run 'pytest' and 'mypy src/veniceresch' before committing the regenerated types."
