#!/usr/bin/env bash
# SE3002 Software Quality Engineering - Automated Setup Script
# Initializes the Docker multi-container stack for pretix, PostgreSQL, and Redis

set -euo pipefail

echo "========================================================"
echo "SE3002 SQE Pretix Setup: Starting Containers & Services"
echo "========================================================"

# Start Docker containers
docker compose up -d

echo "Waiting for services to become healthy..."
docker compose ps

# Wait for Pretix to be ready on port 8345
MAX_RETRIES=30
RETRY_COUNT=0
URL="http://localhost:8345/healthcheck/"

until curl -s -f "$URL" > /dev/null 2>&1 || [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; do
    echo "Waiting for Pretix web service at http://localhost:8345 (attempt $((RETRY_COUNT+1))/$MAX_RETRIES)..."
    sleep 3
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; then
    echo "Warning: Healthcheck endpoint did not respond, checking root URL..."
    curl -I http://localhost:8345/
fi

echo "Pretix container services successfully started!"
