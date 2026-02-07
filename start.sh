#!/bin/bash

cd /home/runner/workspace/backend && python -m uvicorn server:app --host localhost --port 8000 --reload &
BACKEND_PID=$!

cd /home/runner/workspace/frontend && PORT=5000 HOST=0.0.0.0 npx craco start &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
