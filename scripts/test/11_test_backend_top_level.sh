#!/usr/bin/env bash
# Run any top-level tests/test_*.py files not covered by directories

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PY_BIN="python3.11"
command -v "$PY_BIN" >/dev/null 2>&1 || { echo "$PY_BIN not found"; exit 1; }
[[ -f backend/venv/bin/activate ]] || "$PY_BIN" -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt >/dev/null 2>&1 || pip install -r backend/requirements.txt

# Find top-level test files and check if any exist
test_files=$(find tests -maxdepth 1 -type f -name "test_*.py" 2>/dev/null | tr '\n' ' ')
if [[ -z "$test_files" ]]; then 
    echo "✅ No top-level test_*.py files to run"
    deactivate || true
    exit 0
fi

echo "Found top-level test files: $test_files"
pytest -v --tb=short --color=yes $test_files
code=$?

deactivate || true
exit $code
