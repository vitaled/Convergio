#!/usr/bin/env bash
# Run Go tests under backend/ if present

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f backend/go.mod ]]; then echo "No Go module in backend/"; exit 0; fi
if ! command -v go >/dev/null 2>&1; then echo "Go toolchain not found"; exit 1; fi

pushd backend >/dev/null
go test ./...
code=$?
popd >/dev/null

exit $code
