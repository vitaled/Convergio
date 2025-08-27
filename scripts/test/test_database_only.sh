#!/bin/bash

echo "🔄 Running Database and Cost Tracking Tests Only..."
echo "====================================================="

# Run only database-related tests (no frontend required)
python -m pytest \
  tests/e2e/test_database_cost_tracking.py::TestDatabaseCostTracking::test_database_connectivity \
  tests/e2e/test_database_cost_tracking.py::TestDatabaseCostTracking::test_crud_operations \
  tests/e2e/test_database_cost_tracking.py::TestDatabaseCostTracking::test_cost_tracking_accuracy \
  tests/e2e/test_cost_tracking_simple.py::TestCostTrackingSimple::test_cost_tracking_basic \
  tests/e2e/test_cost_tracking_simple.py::TestCostTrackingSimple::test_cost_session_basic \
  tests/e2e/test_cost_tracking_simple.py::TestCostTrackingSimple::test_real_cost_data \
  -v --tb=short

echo ""
echo "✅ Database and Cost Tracking Tests Completed"