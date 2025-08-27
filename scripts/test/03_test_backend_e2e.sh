#!/usr/bin/env bash
# Run backend E2E tests - Core Functionality Suite
# (Ali, AutoGen, Agents, Security, Streaming)

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
FAIL_FAST=${FAIL_FAST:-true}
VERBOSE=${VERBOSE:-false}
[[ "$FAIL_FAST" != "true" ]] && set +e

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
log() { echo -e "$1"; }
success() { log "${GREEN}✅ $1${NC}"; }
err() { log "${RED}❌ $1${NC}"; }
info() { log "${BLUE}ℹ️ $1${NC}"; }

info "Running E2E Core Functionality Tests..."

PY_BIN="python3.11"
command -v "$PY_BIN" >/dev/null 2>&1 || { err "$PY_BIN not found"; exit 1; }
[[ -f backend/venv/bin/activate ]] || "$PY_BIN" -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt >/dev/null 2>&1 || pip install -r backend/requirements.txt

pytest_flags="-v --tb=short --color=yes"
[[ "$VERBOSE" == "true" ]] && pytest_flags+=" -s"
config_arg=""; [[ -f tests/pytest.ini ]] && config_arg="-c tests/pytest.ini" || [[ -f pytest.ini ]] && config_arg="-c pytest.ini"

# Core functionality tests (no database conflicts)
test_files=(
    "tests/e2e/test_ali_proactive_intelligence.py"
    "tests/e2e/test_autogen_integration.py"
    "tests/e2e/test_comprehensive_agent_suite.py"
    "tests/e2e/test_security_validation.py"
    "tests/e2e/test_streaming_e2e.py"
    "tests/e2e/test_end_to_end.py"
)

info "Test files: ${test_files[*]}"

# Run tests individually to avoid conflicts
all_passed=true
for test_file in "${test_files[@]}"; do
    if [[ -f "$test_file" ]]; then
        info "Running: $test_file"
        if ! pytest $pytest_flags "$test_file" $config_arg; then
            err "Failed: $test_file"
            all_passed=false
            [[ "$FAIL_FAST" == "true" ]] && break
        else
            success "Passed: $test_file"
        fi
    else
        info "Skipping (not found): $test_file"
    fi
done

deactivate || true

if [[ "$all_passed" == "true" ]]; then
    success "All E2E Core Functionality tests passed"
    exit 0
else
    err "Some E2E Core Functionality tests failed"
    exit 1
fi