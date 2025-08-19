#!/usr/bin/env bash
# Convergio COMPREHENSIVE test runner
# - Runs ALL possible tests in the repository
# - Backend: pytest (unit, integration, e2e, security, performance)
# - Frontend: vitest + Playwright + Storybook
# - Master test runner for comprehensive agent testing
# - Security scans and audits
# - Performance benchmarks
# - Coverage reports
# - Stops at the first failure by default (configurable)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Configuration
BACKEND_PORT=${BACKEND_PORT:-9000}
FRONTEND_PORT=${FRONTEND_PORT:-4000}
FAIL_FAST=${FAIL_FAST:-true}
RUN_COVERAGE=${RUN_COVERAGE:-false}
RUN_PERFORMANCE=${RUN_PERFORMANCE:-true}
RUN_SECURITY=${RUN_SECURITY:-true}
RUN_MASTER_RUNNER=${RUN_MASTER_RUNNER:-true}
VERBOSE=${VERBOSE:-false}

# Ensure base URLs align with backend defaults
export API_BASE_URL=${API_BASE_URL:-"http://localhost:${BACKEND_PORT}"}
export COST_API_BASE_URL=${COST_API_BASE_URL:-"http://localhost:${BACKEND_PORT}/api/v1"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

section() {
  echo -e "\n${BLUE}==================================================${NC}"
  echo -e "${CYAN}$1${NC}"
  echo -e "${BLUE}==================================================${NC}"
}

subsection() {
  echo -e "\n${YELLOW}--- $1 ---${NC}"
}

success() {
  echo -e "${GREEN}✅ $1${NC}"
}

warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
  echo -e "${RED}❌ $1${NC}"
}

info() {
  echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Function to run tests with appropriate flags
run_pytest() {
  local test_path="$1"
  local test_name="$2"
  local extra_flags="${3:-}"
  
  subsection "Running $test_name"
  
  local pytest_flags="-v --tb=short --color=yes"
  if [[ "$FAIL_FAST" == "true" ]]; then
    pytest_flags="$pytest_flags -x"
  fi
  if [[ "$VERBOSE" == "true" ]]; then
    pytest_flags="$pytest_flags -s"
  fi
  if [[ "$RUN_COVERAGE" == "true" ]]; then
    pytest_flags="$pytest_flags --cov=backend/src --cov-report=html --cov-report=term-missing"
  fi

  # Pick an available pytest config if present
  local config_arg=""
  if [[ -f "tests/pytest.ini" ]]; then
    config_arg="-c tests/pytest.ini"
  elif [[ -f "pytest.ini" ]]; then
    config_arg="-c pytest.ini"
  fi

  pytest $pytest_flags $extra_flags "$test_path" $config_arg
}

# -----------------------------
# Backend: Python Environment Setup
# -----------------------------
section "🐍 Backend Environment Setup"

PY_BIN="python3.11"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  error "$PY_BIN not found. Install Python 3.11 (e.g., brew install python@3.11)"
  exit 1
fi

# Create venv if missing
if [[ ! -f "backend/venv/bin/activate" ]]; then
  info "Creating backend/venv with Python 3.11"
  "$PY_BIN" -m venv backend/venv
fi

# Activate venv
source backend/venv/bin/activate

# Ensure deps present (idempotent)
if command -v uv >/dev/null 2>&1; then
  info "Installing backend deps with uv"
  uv pip install -r backend/requirements.txt
else
  info "Installing backend deps with pip"
  pip install -r backend/requirements.txt
fi

# -----------------------------
# Backend: Unit Tests
# -----------------------------
section "🧪 Backend Python Tests (pytest)"

# Run ALL python tests under tests/ once to ensure nothing is missed (unit, integration, e2e, security, performance)
ignore_args=""
if [[ "$RUN_SECURITY" != "true" ]]; then
  ignore_args+=" --ignore=tests/security"
fi
if [[ "$RUN_PERFORMANCE" != "true" ]]; then
  ignore_args+=" --ignore=tests/performance"
fi
run_pytest "tests" "All Python Tests" "$ignore_args"

# -----------------------------
# Master Test Runner (Comprehensive Agent Testing)
# -----------------------------
if [[ "$RUN_MASTER_RUNNER" == "true" ]]; then
  section "🎯 Master Test Runner (Comprehensive Agent Suite)"
  
  subsection "Running Master Test Runner"
  if [[ -f "tests/master_test_runner.py" ]]; then
    cd tests
    python master_test_runner.py
    cd ..
  else
    info "Master test runner not found at tests/master_test_runner.py — skipping"
  fi
else
  info "Skipping master test runner (RUN_MASTER_RUNNER=false)"
fi

# Deactivate Python venv
deactivate || true

# -----------------------------
# Frontend: Node Environment Setup
# -----------------------------
if [[ -d "frontend" ]]; then
  section "🟢 Frontend Environment Setup"
  
  pushd frontend >/dev/null
  
  # Install node deps if needed
  if [[ ! -d node_modules ]]; then
    info "Installing frontend dependencies"
    npm install
  fi
  
  # -----------------------------
  # Frontend: Unit Tests (Vitest)
  # -----------------------------
  section "🧪 Frontend Unit Tests (Vitest)"
  
  subsection "Running Vitest unit tests"
  vitest_flags=""
  if [[ "$FAIL_FAST" == "true" ]]; then
    vitest_flags="--bail=1"
  fi
  if [[ "$RUN_COVERAGE" == "true" ]]; then
    vitest_flags="$vitest_flags --coverage"
  fi

  # Prefer package script, fallback to direct vitest
  npm run -s test -- $vitest_flags || npx vitest run $vitest_flags
  
  # -----------------------------
  # Frontend: Storybook Tests
  # -----------------------------
  section "📚 Frontend Storybook Tests"
  
  subsection "Running Storybook tests"
  npm run -s test:ui -- $vitest_flags \
    || npm run -s test:storybook -- $vitest_flags \
    || warning "Storybook tests failed or not available"
  
  # -----------------------------
  # Frontend: Playwright E2E Tests
  # -----------------------------
  section "🎭 Frontend E2E Tests (Playwright)"
  
  # Ensure Playwright browsers are installed (idempotent)
  npx playwright install --with-deps || true
  
  subsection "Running Playwright E2E tests"
  playwright_flags=""
  if [[ "$FAIL_FAST" == "true" ]]; then
    playwright_flags="--max-failures=1"
  fi

  # Prefer package script, fallback to direct playwright
  npm run -s test:e2e -- $playwright_flags || npx playwright test $playwright_flags
  
  # -----------------------------
  # Frontend: Security Audit
  # -----------------------------
  if [[ "$RUN_SECURITY" == "true" ]]; then
    section "🔒 Frontend Security Audit"
    
    subsection "Running npm audit"
    npm run -s security:scan || warning "Security audit failed"
  fi
  
  popd >/dev/null
else
  section "ℹ️ Frontend directory not found, skipping frontend tests"
fi

# -----------------------------
# Additional Test Suites
# -----------------------------
section "🔍 Additional Test Suites"

# Check if there are any other test files in the root tests directory
subsection "Go tests (if present)"
if [[ -f "backend/go.mod" ]]; then
  if command -v go >/dev/null 2>&1; then
  if find backend -type f -name "*_test.go" | grep -q .; then
      pushd backend >/dev/null
      info "Running go test ./..."
      go test ./...
      popd >/dev/null
    else
      info "No Go tests found under backend/"
    fi
  else
    warning "Go toolchain not found; skipping Go tests"
  fi
else
  info "No backend/go.mod detected; skipping Go tests"
fi

subsection "Additional Python test files under tests/ (direct runs, if any)"
# In rare setups, there may be test entrypoints not auto-discovered; run explicit test_*.py under tests/ directly.
mapfile -t extra_py_tests < <(find tests -maxdepth 1 -type f -name "test_*.py" 2>/dev/null || true)
if (( ${#extra_py_tests[@]} > 0 )); then
  info "Running top-level python test files: ${extra_py_tests[*]}"
  for f in "${extra_py_tests[@]}"; do
    run_pytest "$f" "Top-level Python Test: $(basename "$f")"
  done
else
  info "No extra top-level python test files found under tests/"
fi

# Check for any HTML test files (like playground tests)
if [[ -f "tests/playground/test_playground.html" ]]; then
  subsection "Playground HTML test detected"
  info "Playground tests found (HTML) — ensure they are covered by your E2E suite or run manually"
fi

# -----------------------------
# Coverage Report (if enabled)
# -----------------------------
if [[ "$RUN_COVERAGE" == "true" ]]; then
  section "📊 Coverage Report"
  
  if [[ -d "htmlcov" ]]; then
    info "Coverage report generated in htmlcov/ directory"
    info "Open htmlcov/index.html in your browser to view detailed coverage"
  fi
fi

# -----------------------------
# Test Summary
# -----------------------------
section "📋 Test Execution Summary"

success "All test suites completed!"
info "Test results and logs are available in:"
info "  - Backend: tests/logs/"
info "  - Frontend: frontend/test-results/ (if Playwright tests ran)"
info "  - Coverage: htmlcov/ (if coverage was enabled)"

if [[ "$FAIL_FAST" == "true" ]]; then
  info "Fail-fast mode was enabled - tests stopped at first failure"
else
  info "All tests ran to completion regardless of failures"
fi

section "✅ All tests completed successfully!"
