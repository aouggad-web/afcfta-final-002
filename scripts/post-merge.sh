#!/bin/bash
set -e

echo "[post-merge] Installing Python dependencies..."
pip install -r backend/requirements.txt --quiet --no-input

echo "[post-merge] Creating required directories..."
mkdir -p backend/data/ai_cache
mkdir -p backend/data/crawled

echo "[post-merge] Installing frontend dependencies..."
cd frontend && npm install --legacy-peer-deps --silent 2>/dev/null || true
cd ..

echo "[post-merge] Done."
