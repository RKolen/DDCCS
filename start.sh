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

# Service ports and URLs — set in .env or environment variables.
GATSBY_PORT="${GATSBY_PORT}"
SIDECAR_PORT="${SIDECAR_PORT}"
DRUPAL_URL="${DRUPAL_URL}"
OLLAMA_PORT="${OLLAMA_PORT}"
MILVUS_PORT="${MILVUS_PORT}"

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
  echo ""
  echo "==> Stopping any existing Gatsby instance on port $GATSBY_PORT..."
  OLD_GATSBY=$(lsof -ti :"$GATSBY_PORT" 2>/dev/null || true)
  if [[ -n "$OLD_GATSBY" ]]; then
    kill "$OLD_GATSBY" 2>/dev/null && echo "    Killed existing process(es): $OLD_GATSBY"
  fi

  echo "==> Clearing Gatsby cache..."
  npm run clean > /dev/null 2>&1

  echo "==> Starting Gatsby dev server (background)..."
  npm run develop > "$SCRIPT_DIR/.gatsby.log" 2>&1 &
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
