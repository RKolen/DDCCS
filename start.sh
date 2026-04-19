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

echo "    Drupal:  https://drupal-cms.ddev.site"
echo "    Ollama:  http://localhost:11434 (inside ddev: http://ddev-drupal-cms-ollama:11434)"
echo "    Milvus:  localhost:19530"

# ---------------------------------------------------------------------------
# 2. Gatsby frontend (dev server in background)
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
  echo "==> Starting Gatsby dev server (background)..."
  npm run develop > "$SCRIPT_DIR/.gatsby.log" 2>&1 &
  GATSBY_PID=$!
  echo "    Gatsby PID: $GATSBY_PID (logs: .gatsby.log)"
  echo "    Frontend:   http://localhost:8000"
  GATSBY_STARTED=true
fi

# ---------------------------------------------------------------------------
# 3. Python consultant CLI (foreground, unless --no-cli)
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
