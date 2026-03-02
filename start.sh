#!/bin/bash

# Determine script directory for portable paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Start backend (bind to 0.0.0.0 so Replit proxy can reach it)
cd "$BACKEND_DIR" && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1 &
BACKEND_PID=$!

# Wait for backend to be ready before starting frontend
echo "Waiting for backend to start on port 8000..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 2
done

# Start frontend
cd "$FRONTEND_DIR" && PORT=5000 HOST=0.0.0.0 npx craco start &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
