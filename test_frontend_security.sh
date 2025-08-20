#!/usr/bin/env bash
# Run frontend security audit (npm audit)

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -d frontend ]]; then echo "frontend/ not found"; exit 1; fi
pushd frontend >/dev/null

if [[ ! -d node_modules ]]; then npm install; fi

npm run -s security:scan || npm audit
code=$?

popd >/dev/null

exit $code
