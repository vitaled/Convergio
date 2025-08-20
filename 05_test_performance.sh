#!/usr/bin/env bash
# Run performance tests (tests/performance)

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
FAIL_FAST=${FAIL_FAST:-true}
VERBOSE=${VERBOSE:-false}
[[ "$FAIL_FAST" != "true" ]] && set +e

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "$1"; }
success() { log "${GREEN}✅ $1${NC}"; }
err() { log "${RED}❌ $1${NC}"; }

PY_BIN="python3.11"
command -v "$PY_BIN" >/dev/null 2>&1 || { err "$PY_BIN not found"; exit 1; }
[[ -f backend/venv/bin/activate ]] || "$PY_BIN" -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt >/dev/null 2>&1 || pip install -r backend/requirements.txt

pytest_flags="-v --tb=short --color=yes"
[[ "$VERBOSE" == "true" ]] && pytest_flags+=" -s"
config_arg=""; [[ -f tests/pytest.ini ]] && config_arg="-c tests/pytest.ini" || [[ -f pytest.ini ]] && config_arg="-c pytest.ini"

pytest $pytest_flags tests/performance $config_arg
code=$?

deactivate || true

(( code == 0 )) && success "Performance tests passed" || { err "Performance tests failed ($code)"; exit $code; }
