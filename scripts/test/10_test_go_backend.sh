#!/usr/bin/env bash
# Run Go tests under backend/ if present

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f backend/go.mod ]]; then echo "No Go module in backend/"; exit 0; fi
if ! command -v go >/dev/null 2>&1; then echo "Go toolchain not found"; exit 1; fi

pushd backend >/dev/null

# Check if there are any Go source files
if ! find . -name "*.go" -not -path "./vendor/*" | head -1 | grep -q "."; then
    echo "✅ No Go source files to test (Go module exists but no .go files)"
    popd >/dev/null
    exit 0
fi

go test ./...
code=$?
popd >/dev/null

exit $code
