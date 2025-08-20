#!/bin/bash

echo "🔄 Running Database Tests Sequentially..."
echo "=========================================="

TESTS=(
  "tests/e2e/test_database_cost_tracking.py::TestDatabaseCostTracking::test_database_connectivity"
  "tests/e2e/test_database_cost_tracking.py::TestDatabaseCostTracking::test_crud_operations" 
  "tests/e2e/test_database_cost_tracking.py::TestDatabaseCostTracking::test_cost_tracking_accuracy"
  "tests/e2e/test_cost_tracking_simple.py::TestCostTrackingSimple::test_cost_tracking_basic"
  "tests/e2e/test_cost_tracking_simple.py::TestCostTrackingSimple::test_real_cost_data"
)

PASSED=0
FAILED=0

for test in "${TESTS[@]}"; do
    echo ""
    echo "🧪 Running: $test"
    echo "----------------------------------------"
    
    if python -m pytest "$test" -v --tb=short; then
        echo "✅ PASSED: $test"
        ((PASSED++))
    else
        echo "❌ FAILED: $test" 
        ((FAILED++))
    fi
done

echo ""
echo "📊 RESULTS:"
echo "============"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "📋 Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 All database tests are working!"
    exit 0
else
    echo ""
    echo "⚠️  Some tests still need attention."
    exit 1
fi