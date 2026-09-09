#!/bin/bash

set -e

# Ports paramétrables par variable d'environnement (défauts inchangés : 8000 /
# 5000). Chaque environnement (Emergent/K8s, sandbox, poste local) fixe les
# siennes dans SON environnement — jamais en patchant ce fichier — pour que
# rien n'ait à être retouché après un `git reset`/déploiement.
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-${VITE_PORT:-5000}}"
export VITE_PORT="$FRONTEND_PORT"
export VITE_BACKEND_URL="${VITE_BACKEND_URL:-http://localhost:$BACKEND_PORT}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

mkdir -p "$SCRIPT_DIR/backend/data/ai_cache"

# Kill any stale dev servers orphaned by a previous run BEFORE starting new ones.
# Without this, leftover processes keep holding the ports, the backend fails to
# bind, Vite falls back to another port, and the preview pane ends up served by
# a stale server -> the preview reloads/flickers constantly.
pkill -f "uvicorn server:app" 2>/dev/null || true
pkill -f "vite --host 0.0.0.0" 2>/dev/null || true
sleep 1

# Cleanly terminate our own children on shutdown/restart so they don't orphan
# and cause the same port conflicts on the next start.
cleanup() {
    trap - TERM INT EXIT
    echo "Shutting down dev servers..."
    pkill -P $$ 2>/dev/null || true
    pkill -f "uvicorn server:app" 2>/dev/null || true
    pkill -f "vite --host 0.0.0.0" 2>/dev/null || true
    exit 0
}
trap cleanup TERM INT EXIT

cd "$BACKEND_DIR" && "$BACKEND_DIR/.venv311/bin/python" -m uvicorn server:app --host 0.0.0.0 --port "$BACKEND_PORT" --workers 1 &
BACKEND_PID=$!

echo "Waiting for backend to start on port $BACKEND_PORT..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 2
done

cd "$FRONTEND_DIR" && npm run start &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
