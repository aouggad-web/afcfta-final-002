#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

mkdir -p "$SCRIPT_DIR/backend/data/ai_cache"

# Kill any stale dev servers orphaned by a previous run BEFORE starting new ones.
# Without this, leftover processes keep holding ports 8000/5000, the backend
# fails to bind 8000, Vite falls back to 5001, and the preview pane (port 5000)
# ends up served by a stale server -> the preview reloads/flickers constantly.
pkill -9 -f "uvicorn server:app" 2>/dev/null || true
pkill -9 -f "vite --host 0.0.0.0 --port 5000" 2>/dev/null || true
sleep 1

# Cleanly terminate our own children on shutdown/restart so they don't orphan
# and cause the same port conflicts on the next start.
cleanup() {
    trap - TERM INT EXIT
    echo "Shutting down dev servers..."
    pkill -P $$ 2>/dev/null || true
    pkill -f "uvicorn server:app" 2>/dev/null || true
    pkill -f "vite --host 0.0.0.0 --port 5000" 2>/dev/null || true
    exit 0
}
trap cleanup TERM INT EXIT

cd "$BACKEND_DIR" && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1 &
BACKEND_PID=$!

echo "Waiting for backend to start on port 8000..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 2
done

cd "$FRONTEND_DIR" && npm run start &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
