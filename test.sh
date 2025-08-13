#!/usr/bin/env bash
# Convergio unified test runner
# - Runs backend (pytest) and frontend (vitest + Playwright) tests
# - Stops at the first failure
# - Mirrors env/ports used by start.sh for API tests

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BACKEND_PORT=${BACKEND_PORT:-9000}
FRONTEND_PORT=${FRONTEND_PORT:-4000}

# Ensure base URLs align with backend defaults
export API_BASE_URL=${API_BASE_URL:-"http://localhost:${BACKEND_PORT}"}
export COST_API_BASE_URL=${COST_API_BASE_URL:-"http://localhost:${BACKEND_PORT}/api/v1"}

section() {
  echo "\n=================================================="
  echo "$1"
  echo "=================================================="
}

# -----------------------------
# Backend: pytest (fail-fast)
# -----------------------------
section "🧪 Backend tests (pytest)"

PY_BIN="python3.11"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  echo "❌ $PY_BIN not found. Install Python 3.11 (e.g., brew install python@3.11)"
  exit 1
fi

# Create venv if missing
if [[ ! -f "backend/venv/bin/activate" ]]; then
  echo "🆕 Creating backend/venv with Python 3.11"
  "$PY_BIN" -m venv backend/venv
fi

# Activate venv
source backend/venv/bin/activate

# Ensure deps present (idempotent)
if command -v uv >/dev/null 2>&1; then
  echo "📦 Installing backend deps with uv"
  uv pip install -r backend/requirements.txt
else
  echo "📦 Installing backend deps with pip"
  pip install -r backend/requirements.txt
fi

# Run pytest with fail-fast using tests config
pytest -x -q -c tests/pytest.ini

deactivate || true

# -----------------------------
# Frontend: vitest (fail-fast)
# -----------------------------
if [[ -d "frontend" ]]; then
  section "🧪 Frontend unit tests (vitest)"
  pushd frontend >/dev/null

  # Install node deps if needed
  if [[ ! -d node_modules ]]; then
    echo "📦 Installing frontend dependencies"
    npm install
  fi

  # Run vitest with bail on first failure
  npm run -s test -- --bail=1
  popd >/dev/null

  # -----------------------------
  # Frontend: Playwright e2e (fail-fast)
  # -----------------------------
  section "🧪 Frontend E2E (Playwright)"
  pushd frontend >/dev/null
  # Ensure Playwright browsers are installed (idempotent)
  npx playwright install --with-deps || true
  npm run -s test:e2e -- --max-failures=1
  popd >/dev/null
else
  section "ℹ️ Frontend directory not found, skipping frontend tests"
fi

section "✅ All tests passed"
