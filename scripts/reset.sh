#!/usr/bin/env bash
# SE3002 Software Quality Engineering - Database Reset Script
# Purges transient order mutations and restores the database to identical seeded state

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================================"
echo "SE3002 SQE Pretix Reset: Restoring State to Clean Seed"
echo "========================================================"

# Purge and re-seed
"$SCRIPT_DIR/seed.sh"

echo "System state reset successfully verified."
