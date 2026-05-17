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

DRUPAL_URL="${DRUPAL_URL:-${DRUPAL_BASE_URL:-https://drupal-cms.ddev.site}}"
GATSBY_HOST="${GATSBY_HOST:-localhost}"
GATSBY_PORT="${GATSBY_PORT:-8000}"
GATSBY_DEFAULT_PORT="${GATSBY_DEFAULT_PORT:-8000}"
GATSBY_CLEAN_ON_START="${GATSBY_CLEAN_ON_START:-true}"
GATSBY_KILL_STALE_LISTENERS="${GATSBY_KILL_STALE_LISTENERS:-true}"
GATSBY_LOG_FILE="${GATSBY_LOG_FILE:-$SCRIPT_DIR/.gatsby.log}"
SIDECAR_HOST="${SIDECAR_HOST:-localhost}"
SIDECAR_PORT="${SIDECAR_PORT:-8765}"
SIDECAR_LOG_FILE="${SIDECAR_LOG_FILE:-$SCRIPT_DIR/.sidecar.log}"
OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
DDEV_OLLAMA_HOST="${DDEV_OLLAMA_HOST:-ddev-drupal-cms-ollama}"
MILVUS_HOST="${MILVUS_HOST:-localhost}"
MILVUS_PORT="${MILVUS_PORT:-19530}"
MKCERT_CA="${MKCERT_CA:-$HOME/.local/share/mkcert/rootCA.pem}"

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
echo "    Ollama:  http://$OLLAMA_HOST:$OLLAMA_PORT (inside ddev: http://$DDEV_OLLAMA_HOST:$OLLAMA_PORT)"
echo "    Milvus:  $MILVUS_HOST:$MILVUS_PORT"

# ---------------------------------------------------------------------------
# 2. Search query parser sidecar (background)
# ---------------------------------------------------------------------------
echo ""
echo "==> Starting search query parser sidecar (background)..."
python3 run_sidecar.py > "$SIDECAR_LOG_FILE" 2>&1 &
SIDECAR_PID=$!
echo "    Sidecar PID: $SIDECAR_PID (logs: $SIDECAR_LOG_FILE)"
echo "    Sidecar:     http://$SIDECAR_HOST:$SIDECAR_PORT"

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
  if [[ "$GATSBY_KILL_STALE_LISTENERS" == "true" ]]; then
    # Only stop processes listening on Gatsby ports. Plain `lsof -ti :PORT`
    # also returns browser clients connected to that port, which can close tabs.
    declare -A CHECKED_PORTS=()
    for PORT in "$GATSBY_DEFAULT_PORT" "$GATSBY_PORT"; do
      [[ -n "${CHECKED_PORTS[$PORT]:-}" ]] && continue
      CHECKED_PORTS[$PORT]=1
      OLD=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
      if [[ -n "$OLD" ]]; then
        kill $OLD 2>/dev/null && echo "    Stopped Gatsby listener(s) on :$PORT - PIDs: $OLD"
        sleep 1
      fi
    done
  fi
  echo ""
  echo "==> Port ${GATSBY_PORT} is free."

  if [[ "$GATSBY_CLEAN_ON_START" == "true" ]]; then
    echo "==> Clearing Gatsby cache..."
    npm run clean > /dev/null 2>&1
  fi

  echo "==> Starting Gatsby dev server (background)..."
  # Answer Gatsby's interactive port-conflict prompt with 'n' via stdin so
  # the background process never blocks waiting for keyboard input.
  # Trust DDEV's mkcert certificate so gatsby-source-graphql can reach site.
  # The snap mkcert (used by VS Code) has a different CAROOT than the system mkcert used by DDEV.
  echo "n" | NODE_EXTRA_CA_CERTS="$MKCERT_CA" npm run develop > "$GATSBY_LOG_FILE" 2>&1 &
  GATSBY_PID=$!
  echo "    Gatsby PID: $GATSBY_PID (logs: $GATSBY_LOG_FILE)"
  echo "    Frontend:   http://$GATSBY_HOST:$GATSBY_PORT"
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
