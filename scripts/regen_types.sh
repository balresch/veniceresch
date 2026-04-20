#!/usr/bin/env bash
# Regenerate src/venice_sdk/_generated.py from Venice's upstream OpenAPI spec.
#
# Usage:
#   bash scripts/regen_types.sh            # fetch fresh swagger, then generate
#   bash scripts/regen_types.sh --offline  # skip fetch; use the pinned vendor copy
set -euo pipefail

SWAGGER_URL="https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml"
VENDORED="vendor/venice-swagger.yaml"
OUT="src/venice_sdk/_generated.py"

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
    --base-class venice_sdk._base_model.VeniceBaseModel \
    --target-python-version 3.10 \
    --use-annotated \
    --use-double-quotes \
    --use-union-operator \
    --use-standard-collections \
    --field-constraints \
    --collapse-root-models \
    --disable-timestamp \
    --custom-file-header "# AUTO-GENERATED from vendor/venice-swagger.yaml. Do not edit by hand."

echo "==> Formatting"
ruff format "$OUT"

echo "==> Done: $OUT"
