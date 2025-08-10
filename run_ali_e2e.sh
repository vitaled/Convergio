#!/usr/bin/env bash
# Orchestrated runner for Ali real E2E tests
# - Sets up Python venv
# - Ensures backend is up
# - Runs unified and ali/vector E2E tests (real OpenAI)
# - Logs any failures verbosely

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
BACKEND_PORT="${BACKEND_PORT:-9000}"
BASE_URL="${BACKEND_BASE_URL:-http://localhost:$BACKEND_PORT}"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
# Reset previous failures log for a clean run
: > "$LOG_DIR/ali_e2e_failures.log"

# 1) Check OPENAI key
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "❌ OPENAI_API_KEY non impostata. Esporta la chiave nell'ambiente o in .env."
  exit 1
fi

# 2) Prepare venv and deps
PY_BIN="python3.11"
if ! command -v "$PY_BIN" &>/dev/null; then
  echo "❌ $PY_BIN non trovato. Installa Python 3.11 (es. 'brew install python@3.11')." >&2
  exit 1
fi
if [[ ! -f "$BACKEND_DIR/venv/bin/activate" ]]; then
  echo "🆕 Creo virtualenv backend/venv"
  "$PY_BIN" -m venv "$BACKEND_DIR/venv"
fi
source "$BACKEND_DIR/venv/bin/activate"
if command -v uv &>/dev/null; then
  uv pip install -r "$BACKEND_DIR/requirements.txt"
else
  pip install -r "$BACKEND_DIR/requirements.txt"
fi

# 3) Ensure backend running
is_backend_up() { curl -sS "$BASE_URL/health" -m 3 -o /dev/null; }
if ! is_backend_up; then
  echo "🚀 Avvio backend su port $BACKEND_PORT"
  # Free the port if a previous uvicorn instance is stuck
  if command -v lsof >/dev/null 2>&1; then
    PIDS=$(lsof -t -i :"$BACKEND_PORT" -sTCP:LISTEN || true)
    if [[ -n "$PIDS" ]]; then
      echo "⚠️  Killing existing processes on port $BACKEND_PORT: $PIDS"
      kill $PIDS || true
      sleep 1
    fi
  fi
  (
    cd "$BACKEND_DIR"
  uvicorn src.main:app --host 0.0.0.0 --port "$BACKEND_PORT" \
      >"$LOG_DIR/backend_e2e_stdout.log" 2>"$LOG_DIR/backend_e2e_stderr.log" &
    echo $! >"$LOG_DIR/backend_e2e.pid"
  )
  # Wait for readiness
  for i in {1..30}; do
    sleep 1
    if is_backend_up; then
      break
    fi
    echo "⏳ Attendo backend ($i/30)" >/dev/null
  done
  if ! is_backend_up; then
    echo "❌ Backend non raggiungibile su $BASE_URL. Log in $LOG_DIR/backend_e2e_stderr.log"
    exit 1
  fi
fi

# 4) Run E2E tests (real)
export RUN_REAL_OPENAI_TESTS=1
export BACKEND_BASE_URL="$BASE_URL"
cd "$BACKEND_DIR"

FAILED=0
run_test() {
  local test_file="$1"
  echo "🧪 Eseguo: $test_file"
  if ! pytest "$test_file" -q -r s; then
    echo "❌ Test fallito: $test_file" | tee -a "$LOG_DIR/ali_e2e_failures.log"
    FAILED=1
  fi
}

# Choose which tests to run: if E2E_ONLY is set, run just that file; otherwise run the full suite in order
if [[ -n "${E2E_ONLY:-}" ]]; then
  TESTS=("$E2E_ONLY")
else
  TESTS=(
    tests/integration/test_real_e2e_ali_vector_openai.py
    tests/integration/test_ali_e2e_real_openai.py
    tests/integration/test_unified_real_e2e.py
    tests/integration/UseCaseBasedEnd2EndTest.py
  )
fi

for t in "${TESTS[@]}"; do
  run_test "$t"
  # Stop immediately on first failure if running sequentially one-by-one
  if [[ "$FAILED" -ne 0 ]]; then
    break
  fi
done

if [[ "$FAILED" -ne 0 ]]; then
  echo "❌ Alcuni test sono falliti. Controlla $LOG_DIR/ali_e2e_failures.log e i log del backend in $LOG_DIR."
  exit 1
fi

echo "✅ Tutti i test E2E reali di Ali sono passati."
