#!/usr/bin/env bash
# Run frontend E2E tests (Playwright)

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
FAIL_FAST=${FAIL_FAST:-true}
[[ "$FAIL_FAST" != "true" ]] && set +e

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "$1"; }
success() { log "${GREEN}✅ $1${NC}"; }
err() { log "${RED}❌ $1${NC}"; }

if [[ ! -d frontend ]]; then err "frontend/ not found"; exit 1; fi
pushd frontend >/dev/null

if [[ ! -d node_modules ]]; then npm install; fi
npx playwright install --with-deps || true
playwright_flags=""; [[ "$FAIL_FAST" == "true" ]] && playwright_flags="--max-failures=1"

npm run -s test:e2e -- $playwright_flags || npx playwright test $playwright_flags
code=$?

popd >/dev/null

(( code == 0 )) && success "Frontend E2E (Playwright) passed" || { err "Frontend E2E (Playwright) failed ($code)"; exit $code; }
