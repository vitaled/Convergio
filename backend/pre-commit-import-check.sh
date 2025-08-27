#!/bin/bash
# Pre-commit hook to validate import paths
# Prevents committing broken import paths

echo "🔍 Validating import paths..."

cd "$(dirname "$0")"

# Run import validation
if ! python validate_imports.py; then
    echo "❌ Import validation failed!"
    echo "📖 See IMPORT_PATH_CONSISTENCY_GUIDE.md for help"
    exit 1
fi

# Test basic import
export PYTHONPATH="$PWD/src"
if ! python -c "from src.main import app; print('✅ Backend imports OK')" 2>/dev/null; then
    echo "❌ Backend main import failed!"
    echo "🔧 Run: python manual_extend_existing.py"
    exit 1
fi

echo "✅ Import validation passed"
exit 0