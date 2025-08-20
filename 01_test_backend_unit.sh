#!/usr/bin/env bash
# Run backend Python unit tests only (tests/backend/unit)
# Usage:
#   FAIL_FAST=false VERBOSE=true ./01_test_backend_unit.sh

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Config
FAIL_FAST=${FAIL_FAST:-true}
VERBOSE=${VERBOSE:-false}
RUN_COVERAGE=${RUN_COVERAGE:-false}

# Continue-on-error mode
if [[ "$FAIL_FAST" != "true" ]]; then
  set +e
fi

# Colors
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "$1"; }
success() { log "${GREEN}✅ $1${NC}"; }
warn() { log "${YELLOW}⚠️  $1${NC}"; }
err() { log "${RED}❌ $1${NC}"; }

# Python env
PY_BIN="python3.11"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  err "$PY_BIN not found. Install Python 3.11 (brew install python@3.11)"; exit 1
fi
if [[ ! -f "backend/venv/bin/activate" ]]; then
  "$PY_BIN" -m venv backend/venv || { err "venv create failed"; exit 1; }
fi
source backend/venv/bin/activate
pip install -r backend/requirements.txt >/dev/null 2>&1 || pip install -r backend/requirements.txt

# Pytest flags
pytest_flags="-v --tb=short --color=yes"
[[ "$VERBOSE" == "true" ]] && pytest_flags+=" -s"
[[ "$RUN_COVERAGE" == "true" ]] && pytest_flags+=" --cov=backend/src --cov-report=term-missing"
config_arg=""; [[ -f tests/pytest.ini ]] && config_arg="-c tests/pytest.ini" || [[ -f pytest.ini ]] && config_arg="-c pytest.ini"

# Run
pytest $pytest_flags tests/backend/unit $config_arg
code=$?

deactivate || true

if (( code != 0 )); then
  err "Backend unit tests failed (exit $code)"; exit $code
else
  success "Backend unit tests passed"
fi
