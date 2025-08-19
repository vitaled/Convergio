#!/usr/bin/env bash
# Convergio MODULAR test runner - Phases approach
# Allows running specific test phases without starting from zero

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Configuration
BACKEND_PORT=${BACKEND_PORT:-9000}
FRONTEND_PORT=${FRONTEND_PORT:-4000}
FAIL_FAST=${FAIL_FAST:-true}
RUN_COVERAGE=${RUN_COVERAGE:-false}
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

show_usage() {
  echo "Usage: $0 [PHASE]"
  echo ""
  echo "Phases:"
  echo "  setup       - Setup backend environment only"
  echo "  backend     - Run backend unit tests only"
  echo "  integration - Run integration tests only"
  echo "  e2e         - Run E2E tests only"
  echo "  frontend    - Run frontend tests only"
  echo "  security    - Run security tests only"
  echo "  performance - Run performance tests only"
  echo "  all         - Run all tests (equivalent to ./test.sh)"
  echo "  count       - Count tests only"
  echo ""
  echo "Environment variables:"
  echo "  FAIL_FAST=false    - Continue on failures"
  echo "  RUN_COVERAGE=true  - Generate coverage reports"
  echo "  VERBOSE=true       - Verbose output"
}

# Phase implementations
phase_setup() {
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
  
  success "Backend environment ready"
}

phase_backend() {
  section "🧪 Backend Unit Tests"
  source backend/venv/bin/activate
  run_pytest "tests/backend/" "Backend Unit Tests"
  success "Backend tests completed"
}

phase_integration() {
  section "🔗 Integration Tests"
  source backend/venv/bin/activate
  run_pytest "tests/integration/" "Integration Tests"
  success "Integration tests completed"
}

phase_e2e() {
  section "🎭 End-to-End Tests"
  source backend/venv/bin/activate
  # Use longer timeout for E2E tests
  PYTEST_TIMEOUT=120 run_pytest "tests/e2e/" "E2E Tests"
  success "E2E tests completed"
}

phase_security() {
  section "🔒 Security Tests"
  source backend/venv/bin/activate
  run_pytest "tests/security/" "Security Tests"
  success "Security tests completed"
}

phase_performance() {
  section "⚡ Performance Tests"
  source backend/venv/bin/activate
  run_pytest "tests/performance/" "Performance Tests"
  success "Performance tests completed"
}

phase_frontend() {
  section "🟢 Frontend Tests"
  
  if [[ ! -d "frontend" ]]; then
    info "Frontend directory not found, skipping frontend tests"
    return 0
  fi
  
  pushd frontend >/dev/null
  
  # Install node deps if needed
  if [[ ! -d node_modules ]]; then
    info "Installing frontend dependencies"
    npm install
  fi
  
  # Unit Tests
  subsection "Running Vitest unit tests"
  vitest_flags=""
  if [[ "$FAIL_FAST" == "true" ]]; then
    vitest_flags="--bail=1"
  fi
  if [[ "$RUN_COVERAGE" == "true" ]]; then
    vitest_flags="$vitest_flags --coverage"
  fi

  npm run -s test -- $vitest_flags || npx vitest run $vitest_flags
  
  # Playwright E2E
  subsection "Running Playwright E2E tests"
  npx playwright install --with-deps || true
  
  playwright_flags=""
  if [[ "$FAIL_FAST" == "true" ]]; then
    playwright_flags="--max-failures=1"
  fi

  npm run -s test:e2e -- $playwright_flags || npx playwright test $playwright_flags
  
  popd >/dev/null
  success "Frontend tests completed"
}

phase_count() {
  section "📊 Test Count Analysis"
  source backend/venv/bin/activate
  
  echo "Test count by category:"
  echo -n "Backend: "
  pytest --collect-only -q tests/backend/ 2>/dev/null | tail -1 | grep -o '[0-9]\+ tests' || echo "0 tests"
  
  echo -n "Integration: "
  pytest --collect-only -q tests/integration/ 2>/dev/null | tail -1 | grep -o '[0-9]\+ tests' || echo "0 tests"
  
  echo -n "E2E: "
  pytest --collect-only -q tests/e2e/ 2>/dev/null | tail -1 | grep -o '[0-9]\+ tests' || echo "0 tests"
  
  echo -n "Security: "
  pytest --collect-only -q tests/security/ 2>/dev/null | tail -1 | grep -o '[0-9]\+ tests' || echo "0 tests"
  
  echo -n "Performance: "
  pytest --collect-only -q tests/performance/ 2>/dev/null | tail -1 | grep -o '[0-9]\+ tests' || echo "0 tests"
  
  echo -n "TOTAL: "
  pytest --collect-only -q tests/ 2>/dev/null | tail -1 | grep -o '[0-9]\+ tests' || echo "0 tests"
}

phase_all() {
  section "🎯 Running ALL Test Phases"
  phase_setup
  phase_backend
  phase_integration
  phase_security
  phase_performance
  phase_e2e
  
  if [[ -d "frontend" ]]; then
    phase_frontend
  fi
  
  section "✅ All test phases completed!"
}

# Main execution
if [[ $# -eq 0 ]]; then
  show_usage
  exit 1
fi

PHASE="$1"

case "$PHASE" in
  setup)
    phase_setup
    ;;
  backend)
    phase_setup
    phase_backend
    ;;
  integration)
    phase_setup
    phase_integration
    ;;
  e2e)
    phase_setup
    phase_e2e
    ;;
  security)
    phase_setup
    phase_security
    ;;
  performance)
    phase_setup
    phase_performance
    ;;
  frontend)
    phase_frontend
    ;;
  count)
    phase_count
    ;;
  all)
    phase_all
    ;;
  *)
    error "Unknown phase: $PHASE"
    show_usage
    exit 1
    ;;
esac