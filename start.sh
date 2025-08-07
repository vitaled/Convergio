#!/usr/bin/env bash
# Convergio local development launcher (shell wrapper)
# -----------------------------------------------
# 1. Attiva la virtualenv del backend se esiste
# 2. Avvia lo startup Python script
# -----------------------------------------------
set -euo pipefail

# Posizionati nella root del progetto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

# Esegui lo script di startup Python
python scripts/start.py "$@"
