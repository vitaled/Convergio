#!/usr/bin/env bash
# Run frontend Storybook tests if available

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
FAIL_FAST=${FAIL_FAST:-true}
[[ "$FAIL_FAST" != "true" ]] && set +e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "$1"; }
success() { log "${GREEN}✅ $1${NC}"; }
warn() { log "${YELLOW}⚠️  $1${NC}"; }
err() { log "${RED}❌ $1${NC}"; }

if [[ ! -d frontend ]]; then err "frontend/ not found"; exit 1; fi
pushd frontend >/dev/null

if [[ ! -d node_modules ]]; then npm install; fi

npm run -s test:ui || npm run -s test:storybook
code=$?

popd >/dev/null

if (( code == 0 )); then success "Frontend Storybook tests passed"; else err "Frontend Storybook tests failed ($code)"; exit $code; fi
