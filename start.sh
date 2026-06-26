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

# Use the project virtualenv interpreter: the sidecar and CLI need openai,
# tenacity, and beautifulsoup4, which are installed in .venv but not in the
# system python. Falls back to python3 only when .venv is absent.
PYTHON="$SCRIPT_DIR/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="python3"

# Load .env so port/URL variables are available before use.
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/.env"
  set +a
fi

# Service hosts/ports are authoritative in .env. Fail loudly (set -u + :?) when
# a required value is missing rather than masking it with a hardcoded default.
DRUPAL_URL="${DRUPAL_URL:?set DRUPAL_URL (or DRUPAL_BASE_URL) in .env}"
GATSBY_HOST="${GATSBY_HOST:?set GATSBY_HOST in .env}"
GATSBY_PORT="${GATSBY_PORT:?set GATSBY_PORT in .env}"
SIDECAR_HOST="${SIDECAR_HOST:?set SIDECAR_HOST in .env}"
SIDECAR_PORT="${SIDECAR_PORT:?set SIDECAR_PORT in .env}"
OLLAMA_HOST="${OLLAMA_HOST:?set OLLAMA_HOST in .env}"
OLLAMA_PORT="${OLLAMA_PORT:?set OLLAMA_PORT in .env}"
DDEV_OLLAMA_HOST="${DDEV_OLLAMA_HOST:?set DDEV_OLLAMA_HOST in .env}"
MILVUS_HOST="${MILVUS_HOST:?set MILVUS_HOST in .env}"
MILVUS_PORT="${MILVUS_PORT:?set MILVUS_PORT in .env}"

# Operational knobs (local script behaviour, not service configuration).
GATSBY_DEFAULT_PORT="${GATSBY_DEFAULT_PORT:-$GATSBY_PORT}"
GATSBY_CLEAN_ON_START="${GATSBY_CLEAN_ON_START:-true}"
GATSBY_KILL_STALE_LISTENERS="${GATSBY_KILL_STALE_LISTENERS:-true}"
GATSBY_LOG_FILE="${GATSBY_LOG_FILE:-$SCRIPT_DIR/.gatsby.log}"
SIDECAR_LOG_FILE="${SIDECAR_LOG_FILE:-$SCRIPT_DIR/.sidecar.log}"
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
# Run from the project root so run_sidecar.py is found and .env / game_data
# resolve correctly (ddev start left us in drupal-cms/).
cd "$SCRIPT_DIR"
"$PYTHON" "$SCRIPT_DIR/run_sidecar.py" > "$SIDECAR_LOG_FILE" 2>&1 &
SIDECAR_PID=$!
echo "    Sidecar PID: $SIDECAR_PID (logs: $SIDECAR_LOG_FILE)"
# Verify it actually bound; surface import/CWD/port errors instead of dying silently.
sleep 2
if curl -sf --max-time 2 "http://$SIDECAR_HOST:$SIDECAR_PORT/health" >/dev/null 2>&1; then
  echo "    Sidecar:     http://$SIDECAR_HOST:$SIDECAR_PORT (healthy)"
else
  echo "    WARNING: sidecar did not come up (port $SIDECAR_PORT in use, or an error)."
  echo "    Last log lines ($SIDECAR_LOG_FILE):"
  tail -3 "$SIDECAR_LOG_FILE" 2>/dev/null | sed 's/^/      /'
  echo "    If another project uses port $SIDECAR_PORT, set SIDECAR_PORT in .env to a free port."
fi

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
  echo "All background services started. Run '$PYTHON dnd_consultant.py' to open the CLI."
  exit 0
fi

echo ""
echo "==> Starting D&D Character Consultant..."
echo "    Press Ctrl+C to exit (background services will keep running)."
echo ""
"$PYTHON" dnd_consultant.py

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
