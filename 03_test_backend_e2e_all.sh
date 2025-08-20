#!/usr/bin/env bash
# Run all backend E2E tests in separate suites to avoid conflicts

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; YELLOW='\033[0;33m'; NC='\033[0m'
log() { echo -e "$1"; }
success() { log "${GREEN}✅ $1${NC}"; }
err() { log "${RED}❌ $1${NC}"; }
info() { log "${BLUE}ℹ️ $1${NC}"; }
warn() { log "${YELLOW}⚠️ $1${NC}"; }

info "🚀 Running Complete E2E Test Suite (Split for SQLAlchemy Compatibility)"
echo "============================================================================="

# Track overall results
overall_success=true
suite1_result=0
suite2_result=0

# Run Suite 1: Core Functionality
info "📋 Suite 1/2: Core Functionality Tests"
echo "------------------------------------"
if ./03_test_backend_e2e.sh; then
    success "Suite 1 PASSED: Core Functionality"
    suite1_result=0
else
    err "Suite 1 FAILED: Core Functionality"
    suite1_result=1
    overall_success=false
fi

echo ""
info "⏳ Waiting 3 seconds between suites..."
sleep 3
echo ""

# Run Suite 2: Database & Cost Tracking
info "💰 Suite 2/2: Database & Cost Tracking Tests"  
echo "--------------------------------------------"
if ./03a_test_backend_e2e.sh; then
    success "Suite 2 PASSED: Database & Cost Tracking"
    suite2_result=0
else
    err "Suite 2 FAILED: Database & Cost Tracking"
    suite2_result=1
    overall_success=false
fi

echo ""
echo "============================================================================="
info "📊 E2E Test Suite Results:"
echo "  Suite 1 (Core Functionality): $([[ $suite1_result -eq 0 ]] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "  Suite 2 (Database & Cost):    $([[ $suite2_result -eq 0 ]] && echo "✅ PASSED" || echo "❌ FAILED")"
echo ""

if [[ "$overall_success" == "true" ]]; then
    success "🎉 ALL E2E TEST SUITES PASSED!"
    exit 0
else
    err "❌ Some E2E test suites failed"
    warn "💡 Tip: Run individual suites with ./03_test_backend_e2e.sh or ./03a_test_backend_e2e.sh"
    exit 1
fi