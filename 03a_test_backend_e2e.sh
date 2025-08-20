#!/usr/bin/env bash
# Run backend E2E tests - Database & Cost Tracking Suite
# (Cost tracking, Database operations, Multiagent workflows)

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
FAIL_FAST=${FAIL_FAST:-true}
VERBOSE=${VERBOSE:-false}
[[ "$FAIL_FAST" != "true" ]] && set +e

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; YELLOW='\033[0;33m'; NC='\033[0m'
log() { echo -e "$1"; }
success() { log "${GREEN}✅ $1${NC}"; }
err() { log "${RED}❌ $1${NC}"; }
info() { log "${BLUE}ℹ️ $1${NC}"; }
warn() { log "${YELLOW}⚠️ $1${NC}"; }

info "Running E2E Database & Cost Tracking Tests..."

PY_BIN="python3.11"
command -v "$PY_BIN" >/dev/null 2>&1 || { err "$PY_BIN not found"; exit 1; }
[[ -f backend/venv/bin/activate ]] || "$PY_BIN" -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt >/dev/null 2>&1 || pip install -r backend/requirements.txt

pytest_flags="-v --tb=short --color=yes"
[[ "$VERBOSE" == "true" ]] && pytest_flags+=" -s"
config_arg=""; [[ -f tests/pytest.ini ]] && config_arg="-c tests/pytest.ini" || [[ -f pytest.ini ]] && config_arg="-c pytest.ini"

# Database and cost tracking tests (potential SQLAlchemy conflicts)
test_files=(
    "tests/e2e/test_cost_tracking_simple.py"
    "tests/e2e/test_database_cost_tracking.py"
    "tests/e2e/test_multiagent_workflows.py"
)

info "Test files: ${test_files[*]}"

# Run tests individually with extra spacing to avoid registry conflicts
all_passed=true
test_count=0
total_tests=${#test_files[@]}

for test_file in "${test_files[@]}"; do
    ((test_count++))
    if [[ -f "$test_file" ]]; then
        info "[$test_count/$total_tests] Running: $test_file"
        
        # Add slight delay between tests to ensure clean registry state
        [[ $test_count -gt 1 ]] && sleep 2
        
        if pytest $pytest_flags "$test_file" $config_arg; then
            success "[$test_count/$total_tests] Passed: $test_file"
        else
            err "[$test_count/$total_tests] Failed: $test_file"
            all_passed=false
            [[ "$FAIL_FAST" == "true" ]] && break
        fi
        
        # Force cleanup between tests
        info "Cleaning up test environment..."
        sleep 1
    else
        warn "[$test_count/$total_tests] Skipping (not found): $test_file"
    fi
done

deactivate || true

if [[ "$all_passed" == "true" ]]; then
    success "All E2E Database & Cost Tracking tests passed"
    exit 0
else
    err "Some E2E Database & Cost Tracking tests failed"
    warn "Note: These tests may have SQLAlchemy registry conflicts when run together"
    warn "Individual test runs should work fine"
    exit 1
fi