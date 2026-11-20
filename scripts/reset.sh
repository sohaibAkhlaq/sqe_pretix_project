#!/usr/bin/env bash
# SE3002 Software Quality Engineering - Database Reset Script
# Purges transient order mutations and restores the database to identical seeded state
# Empirically verifies reset idempotency via dual execution.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================================"
echo "SE3002 SQE Pretix Reset: Restoring State to Clean Seed"
echo "========================================================"

if [ -f "$PROJECT_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/Scripts/python.exe"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON_BIN="python"
fi

"$PYTHON_BIN" "$SCRIPT_DIR/reset.py" --verify-idempotency

echo "System state reset and idempotency successfully verified."
