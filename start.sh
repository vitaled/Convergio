#!/usr/bin/env bash
# Convergio local development launcher (shell wrapper)
# -----------------------------------------------
# 1. Kill processes on designated ports (backend:9000, frontend:4000)
# 2. Attiva la virtualenv del backend se esiste  
# 3. Avvia backend e frontend sulle porte fisse
# -----------------------------------------------
set -euo pipefail

# Posizionati nella root del progetto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ----------------------------------------------------------------------------------
# Fixed ports configuration
# ----------------------------------------------------------------------------------
BACKEND_PORT=9000
FRONTEND_PORT=4000

echo "🚀 CONVERGIO - LOCAL DEVELOPMENT STARTUP"
echo "=================================================="
echo "🎯 Backend: http://localhost:$BACKEND_PORT"
echo "🎨 Frontend: http://localhost:$FRONTEND_PORT"
echo "=================================================="

# ----------------------------------------------------------------------------------
# Kill processes on designated ports
# ----------------------------------------------------------------------------------
kill_port_process() {
  local port=$1
  local service=$2
  
  echo "🔍 Checking for processes on port $port..."
  local pids=$(lsof -ti:$port 2>/dev/null || true)
  
  if [[ -n "$pids" ]]; then
    echo "⚡ Killing existing $service processes on port $port: $pids"
    kill -9 $pids 2>/dev/null || true
    sleep 1
    echo "✅ Port $port cleared"
  else
    echo "✅ Port $port is free"
  fi
}

kill_port_process $BACKEND_PORT "backend"
kill_port_process $FRONTEND_PORT "frontend"

# ----------------------------------------------------------------------------------
# Virtualenv management (Python 3.11 required)
# ----------------------------------------------------------------------------------
PY_BIN="python3.11"
if ! command -v "$PY_BIN" &>/dev/null; then
  echo "❌ $PY_BIN non trovato. Installa Python 3.11 (es. 'brew install python@3.11') e riprova." >&2
  exit 1
fi

# (Re)create venv if missing or with wrong python version
if [[ ! -f backend/venv/bin/activate ]]; then
  echo "🆕 Creazione virtualenv backend/venv con Python 3.11"
  "$PY_BIN" -m venv backend/venv
fi

# Attiva venv
source backend/venv/bin/activate
VENV_PY_VER=$(python -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))')
if [[ "$VENV_PY_VER" != "3.11" ]]; then
  echo "⚠️  Virtualenv usa Python $VENV_PY_VER: la ricreo con 3.11"
  deactivate || true
  rm -rf backend/venv
  "$PY_BIN" -m venv backend/venv
  source backend/venv/bin/activate
fi

# ----------------------------------------------------------------------------------
# Activate virtual environment CRITICAL for uvicorn to work
# ----------------------------------------------------------------------------------
if [[ -f "backend/venv/bin/activate" ]]; then
  echo "🐍 Activating Python virtual environment..."
  source backend/venv/bin/activate
  echo "✅ Virtual environment activated: $(which python)"
else
  echo "❌ Virtual environment not found at backend/venv/"
  echo "Please run: cd backend && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# Install requirements (sempre, per evitare moduli mancanti)
# ----------------------------------------------------------------------------------
if command -v uv &>/dev/null; then
  echo "📦 Installazione/aggiornamento dipendenze con uv (più veloce)"
  uv pip install -r backend/requirements.txt
else
  echo "📦 Installazione/aggiornamento dipendenze con pip"
  pip install -r backend/requirements.txt
fi

# Rimuovi eventuali vecchie virtualenv stray (.venv, venv) non più usate
for d in .venv venv; do
  if [[ -d "$d" && "$d" != "backend/venv" ]]; then
    echo "🧹 Rimozione vecchio ambiente $d"
    rm -rf "$d"
  fi
done

# ----------------------------------------------------------------------------------
# System checks and startup
# ----------------------------------------------------------------------------------
echo "🔍 Running system checks..."
python scripts/start.py --check-only

if [[ $? -ne 0 ]]; then
  echo "❌ System checks failed. Please fix the issues above."
  exit 1
fi

echo "✅ All system checks passed!"
echo ""

# ----------------------------------------------------------------------------------  
# Start Backend and Frontend on fixed ports
# ----------------------------------------------------------------------------------
echo "🚀 Starting backend on port $BACKEND_PORT..."
cd backend
uvicorn src.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 8

# Check if backend is responding
if ! curl -s http://localhost:$BACKEND_PORT/health/ >/dev/null; then
  echo "❌ Backend failed to start on port $BACKEND_PORT"
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
fi

echo "✅ Backend running on http://localhost:$BACKEND_PORT"

# Start frontend if directory exists
if [[ -d "frontend" ]]; then
  echo "🎨 Starting frontend on port $FRONTEND_PORT..."
  cd frontend
  
  # Install frontend dependencies if needed
  if [[ ! -d "node_modules" ]]; then
    echo "📦 Installing frontend dependencies..."
    npm install
  fi
  
  # Start frontend
  npm run dev -- --port $FRONTEND_PORT --host 0.0.0.0 &
  FRONTEND_PID=$!
  cd ..
  
  echo "✅ Frontend starting on http://localhost:$FRONTEND_PORT"
else
  echo "⚠️ Frontend directory not found, running backend only"
  FRONTEND_PID=""
fi

# ----------------------------------------------------------------------------------
# Keep processes running and handle cleanup
# ----------------------------------------------------------------------------------
echo ""
echo "🎉 Convergio is running!"
echo "📱 Backend:  http://localhost:$BACKEND_PORT"
echo "📱 API Docs: http://localhost:$BACKEND_PORT/docs"
if [[ -n "$FRONTEND_PID" ]]; then
  echo "🎨 Frontend: http://localhost:$FRONTEND_PORT"
fi
echo ""
echo "Press Ctrl+C to stop all services..."

# Trap cleanup function
cleanup() {
  echo ""
  echo "🛑 Shutting down services..."
  if [[ -n "$BACKEND_PID" ]]; then
    kill $BACKEND_PID 2>/dev/null || true
    echo "✅ Backend stopped"
  fi
  if [[ -n "$FRONTEND_PID" ]]; then
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Frontend stopped" 
  fi
  echo "👋 Goodbye!"
  exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
