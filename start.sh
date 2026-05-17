#!/usr/bin/env bash
# Start all D&D Character Consultant systems.
#
# Usage:
#   ./start.sh          # start everything, then open the Python CLI
#   ./start.sh --no-cli # start background services only (useful for dev)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
DRUPAL_DIR="$SCRIPT_DIR/drupal-cms"

# Load .env so port/URL variables are available before use.
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/.env"
  set +a
fi

NO_CLI=false
for arg in "$@"; do
  [[ "$arg" == "--no-cli" ]] && NO_CLI=true
done

# ---------------------------------------------------------------------------
# 1. Drupal CMS + all DDEV services (Ollama, Milvus, Solr)
# ---------------------------------------------------------------------------
echo "==> Starting Drupal CMS (+ Ollama, Milvus, Solr via DDEV)..."
cd "$DRUPAL_DIR"
ddev start

echo "    Drupal:  $DRUPAL_URL"
echo "    Ollama:  http://localhost:$OLLAMA_PORT (inside ddev: http://ddev-drupal-cms-ollama:$OLLAMA_PORT)"
echo "    Milvus:  localhost:$MILVUS_PORT"

# ---------------------------------------------------------------------------
# 2. Search query parser sidecar (background)
# ---------------------------------------------------------------------------
echo ""
echo "==> Starting search query parser sidecar (background)..."
python3 run_sidecar.py > "$SCRIPT_DIR/.sidecar.log" 2>&1 &
SIDECAR_PID=$!
echo "    Sidecar PID: $SIDECAR_PID (logs: .sidecar.log)"
echo "    Sidecar:     http://localhost:$SIDECAR_PORT"

# ---------------------------------------------------------------------------
# 3. Gatsby frontend (dev server in background)
# ---------------------------------------------------------------------------
cd "$FRONTEND_DIR"

if [[ ! -f ".env.development" ]]; then
  echo ""
  echo "  WARNING: frontend/.env.development not found."
  echo "  Copy frontend/.env.example to frontend/.env.development and fill in DRUPAL_PASSWORD."
  echo "  Skipping Gatsby dev server."
  GATSBY_STARTED=false
else
  # Always kill port 8000 (the Gatsby dev server port) regardless of $GATSBY_PORT.
  # Running `npm run develop` manually without this script leaves stale processes
  # that serve old broken bundles even after code changes.
  for PORT in 8000 "${GATSBY_PORT}"; do
    OLD=$(lsof -ti :"$PORT" 2>/dev/null || true)
    if [[ -n "$OLD" ]]; then
      kill "$OLD" 2>/dev/null && echo "    Killed existing process(es) on :$PORT — PIDs: $OLD"
      for i in {1..10}; do
        lsof -ti :"$PORT" > /dev/null 2>&1 || break
        sleep 1
      done
    fi
  done
  echo ""
  echo "==> Port ${GATSBY_PORT} is free."

  echo "==> Clearing Gatsby cache..."
  npm run clean > /dev/null 2>&1

  echo "==> Starting Gatsby dev server (background)..."
  # Answer Gatsby's interactive port-conflict prompt with 'n' via stdin so
  # the background process never blocks waiting for keyboard input.
  echo "n" | npm run develop > "$SCRIPT_DIR/.gatsby.log" 2>&1 &
  GATSBY_PID=$!
  echo "    Gatsby PID: $GATSBY_PID (logs: .gatsby.log)"
  echo "    Frontend:   http://localhost:$GATSBY_PORT"
  GATSBY_STARTED=true
fi

# ---------------------------------------------------------------------------
# 4. Python consultant CLI (foreground, unless --no-cli)
# ---------------------------------------------------------------------------
cd "$SCRIPT_DIR"

if [[ "$NO_CLI" == true ]]; then
  echo ""
  echo "All background services started. Run 'python3 dnd_consultant.py' to open the CLI."
  exit 0
fi

echo ""
echo "==> Starting D&D Character Consultant..."
echo "    Press Ctrl+C to exit (background services will keep running)."
echo ""
python3 dnd_consultant.py

# On CLI exit, offer to stop background services.
echo ""
read -r -p "Stop search query parser sidecar? [y/N] " stop_sidecar
if [[ "${stop_sidecar,,}" == "y" ]]; then
  kill "$SIDECAR_PID" 2>/dev/null && echo "Sidecar stopped."
fi

if [[ "${GATSBY_STARTED:-false}" == true ]]; then
  read -r -p "Stop Gatsby dev server? [y/N] " stop_gatsby
  if [[ "${stop_gatsby,,}" == "y" ]]; then
    kill "$GATSBY_PID" 2>/dev/null && echo "Gatsby stopped."
  fi
fi

read -r -p "Stop DDEV (Drupal + Milvus + Solr + Ollama)? [y/N] " stop_ddev
if [[ "${stop_ddev,,}" == "y" ]]; then
  cd "$DRUPAL_DIR" && ddev stop
fi
