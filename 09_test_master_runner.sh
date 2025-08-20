#!/usr/bin/env bash
# Run the master test runner script if present

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

if [[ -f tests/master_test_runner.py ]]; then
  pushd tests >/dev/null
  python master_test_runner.py
  code=$?
  popd >/dev/null
  (( code == 0 )) && success "Master Test Runner passed" || { err "Master Test Runner failed ($code)"; exit $code; }
else
  warn "tests/master_test_runner.py not found"
fi
