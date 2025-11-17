#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
HOST=${HOST:-0.0.0.0}
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

cleanup() {
  echo "Stopping backend process..."
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

start_backend() {
  echo "Starting backend on http://$HOST:$BACKEND_PORT..."
  (cd "$ROOT_DIR/backend" && PYTHONPATH="$ROOT_DIR" uvicorn backend.app.main:app --reload --host "$HOST" --port "$BACKEND_PORT" >/tmp/backend.log 2>&1) &
  BACKEND_PID=$!
}

wait_for_backend() {
  echo -n "Waiting for backend health..."
  local retries=30
  while (( retries > 0 )); do
    if curl -fs "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null; then
      echo " done."
      return 0
    fi
    echo -n "."
    sleep 1
    ((retries--))
  done
  echo ""
  echo "Backend did not become healthy within timeout. Check /tmp/backend.log for details." >&2
  return 1
}

start_frontend() {
  echo "Starting frontend on http://$HOST:$FRONTEND_PORT..."
  cd "$ROOT_DIR/frontend"
  npm run dev -- --host "$HOST" --port "$FRONTEND_PORT"
}

start_backend
wait_for_backend
start_frontend
