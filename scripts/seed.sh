#!/usr/bin/env bash
# SE3002 Software Quality Engineering - Data Seeding Script
# Seeds Organizer, Event, Items, Quotas, and Roles for Order/Quota Workflows

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================================"
echo "SE3002 SQE Pretix Seeding: Generating Deterministic Records"
echo "========================================================"

if [ -f "$PROJECT_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/Scripts/python.exe"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON_BIN="python"
fi

"$PYTHON_BIN" "$SCRIPT_DIR/seed.py"

echo "Seeding completed successfully."
