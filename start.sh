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
SIDECAR_KILL_STALE_LISTENERS="${SIDECAR_KILL_STALE_LISTENERS:-true}"
SIDECAR_LOG_FILE="${SIDECAR_LOG_FILE:-$SCRIPT_DIR/.sidecar.log}"
MKCERT_CA="${MKCERT_CA:-$HOME/.local/share/mkcert/rootCA.pem}"
COMFYUI_KILL_STALE_LISTENERS="${COMFYUI_KILL_STALE_LISTENERS:-true}"
COMFYUI_LOG_FILE="${COMFYUI_LOG_FILE:-$SCRIPT_DIR/.comfyui.log}"
JOB_QUEUE_ENABLED="${JOB_QUEUE_ENABLED:-true}"
JOB_QUEUE_LOG_FILE="${JOB_QUEUE_LOG_FILE:-$SCRIPT_DIR/.jobqueue.log}"

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
# Stop any stale sidecar still holding the port. Without this a new sidecar
# fails to bind ("address already in use") and dies, leaving the OLD process
# serving outdated code - so restarts silently have no effect. LISTEN-only so
# connected clients are never killed (same guard as the Gatsby block).
if [[ "$SIDECAR_KILL_STALE_LISTENERS" == "true" ]]; then
  OLD_SIDECAR=$(lsof -tiTCP:"$SIDECAR_PORT" -sTCP:LISTEN 2>/dev/null || true)
  if [[ -n "$OLD_SIDECAR" ]]; then
    kill $OLD_SIDECAR 2>/dev/null && echo "    Stopped stale sidecar on :$SIDECAR_PORT - PIDs: $OLD_SIDECAR"
    sleep 1
  fi
fi
# MKCERT_CA lets the sidecar verify ddev's mkcert-signed TLS for Drupal reads.
MKCERT_CA="$MKCERT_CA" "$PYTHON" "$SCRIPT_DIR/run_sidecar.py" > "$SIDECAR_LOG_FILE" 2>&1 &
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
# 3. ComfyUI portrait service (host, background) - only when COMFYUI_ENABLED
# ---------------------------------------------------------------------------
# ComfyUI is opt-in: skipped entirely unless COMFYUI_ENABLED=true. It runs from
# its own install (COMFYUI_DIR) with its own venv, on the host like Ollama - the
# sidecar reaches it over its HTTP workflow API to generate character portraits.
COMFYUI_STARTED=false
if [[ "${COMFYUI_ENABLED:-}" == "true" ]]; then
  # Required only in this branch; fail loudly rather than guess a path/port.
  COMFYUI_HOST="${COMFYUI_HOST:?set COMFYUI_HOST in .env (COMFYUI_ENABLED=true)}"
  COMFYUI_PORT="${COMFYUI_PORT:?set COMFYUI_PORT in .env (COMFYUI_ENABLED=true)}"
  COMFYUI_DIR="${COMFYUI_DIR:?set COMFYUI_DIR in .env to your ComfyUI install path}"
  COMFYUI_EXTRA_ARGS="${COMFYUI_EXTRA_ARGS:-}"

  echo ""
  echo "==> Starting ComfyUI portrait service (background)..."
  # Free a stale ComfyUI still holding the port (LISTEN-only, same guard as the
  # sidecar block) so a restart binds instead of dying "address already in use".
  if [[ "$COMFYUI_KILL_STALE_LISTENERS" == "true" ]]; then
    OLD_COMFYUI=$(lsof -tiTCP:"$COMFYUI_PORT" -sTCP:LISTEN 2>/dev/null || true)
    if [[ -n "$OLD_COMFYUI" ]]; then
      kill $OLD_COMFYUI 2>/dev/null && echo "    Stopped stale ComfyUI on :$COMFYUI_PORT - PIDs: $OLD_COMFYUI"
      sleep 1
    fi
  fi

  # ComfyUI has its own venv (its deps differ from the project's); fall back to
  # python3 only when that venv is absent.
  COMFYUI_PYTHON="$COMFYUI_DIR/venv/bin/python"
  [[ -x "$COMFYUI_PYTHON" ]] || COMFYUI_PYTHON="python3"

  # Optional launch flags (e.g. --cpu, --listen) come from COMFYUI_EXTRA_ARGS.
  COMFYUI_ARGS=()
  [[ -n "$COMFYUI_EXTRA_ARGS" ]] && read -ra COMFYUI_ARGS <<< "$COMFYUI_EXTRA_ARGS"

  # exec so $! is the python PID (killable), not the transient subshell's.
  ( cd "$COMFYUI_DIR" && exec "$COMFYUI_PYTHON" main.py --port "$COMFYUI_PORT" "${COMFYUI_ARGS[@]}" ) \
    > "$COMFYUI_LOG_FILE" 2>&1 &
  COMFYUI_PID=$!
  COMFYUI_STARTED=true
  echo "    ComfyUI PID: $COMFYUI_PID (logs: $COMFYUI_LOG_FILE)"

  # Readiness probe: CPU startup + model index can take a few seconds.
  COMFYUI_READY=false
  for _ in $(seq 1 15); do
    if curl -sf --max-time 2 "http://$COMFYUI_HOST:$COMFYUI_PORT/system_stats" >/dev/null 2>&1; then
      COMFYUI_READY=true
      break
    fi
    sleep 1
  done
  if [[ "$COMFYUI_READY" == true ]]; then
    echo "    ComfyUI:     http://$COMFYUI_HOST:$COMFYUI_PORT (healthy)"
  else
    echo "    WARNING: ComfyUI did not come up on :$COMFYUI_PORT (portraits will 503)."
    echo "    Last log lines ($COMFYUI_LOG_FILE):"
    tail -3 "$COMFYUI_LOG_FILE" 2>/dev/null | sed 's/^/      /'
  fi
fi

# ---------------------------------------------------------------------------
# 4. Gatsby frontend (dev server in background)
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
# 5. AI job queue processor (host, background)
# ---------------------------------------------------------------------------
# One processor, one job at a time: this is what serializes the heavy AI work so
# two large models are never resident at once on this CPU-only box. It runs
# after Gatsby because arc/story/summary jobs call the console's API routes.
# The drush command polls the queue and blocks; the loop restarts it if it ever
# exits (a DB blip, a config change picked up on the next bootstrap).
JOB_QUEUE_STARTED=false
if [[ "$JOB_QUEUE_ENABLED" == "true" ]]; then
  echo ""
  echo "==> Starting AI job queue processor (background)..."
  cd "$DRUPAL_DIR"
  (
    while true; do
      ddev drush advancedqueue:queue:process dnd_ai --timeout=0
      echo "[start.sh] queue processor exited; restarting in 5s"
      sleep 5
    done
  ) > "$JOB_QUEUE_LOG_FILE" 2>&1 &
  JOB_QUEUE_PID=$!
  JOB_QUEUE_STARTED=true
  echo "    Queue PID:  $JOB_QUEUE_PID (logs: $JOB_QUEUE_LOG_FILE)"
  echo "    Queue:      dnd_ai (portraits, arcs, stories, summaries - one at a time)"
fi

# ---------------------------------------------------------------------------
# 6. Python consultant CLI (foreground, unless --no-cli)
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

if [[ "${COMFYUI_STARTED:-false}" == true ]]; then
  read -r -p "Stop ComfyUI portrait service? [y/N] " stop_comfyui
  if [[ "${stop_comfyui,,}" == "y" ]]; then
    kill "$COMFYUI_PID" 2>/dev/null && echo "ComfyUI stopped."
  fi
fi

if [[ "${JOB_QUEUE_STARTED:-false}" == true ]]; then
  read -r -p "Stop AI job queue processor? [y/N] " stop_queue
  if [[ "${stop_queue,,}" == "y" ]]; then
    # Kill the restart loop first, then the drush process it supervises.
    kill "$JOB_QUEUE_PID" 2>/dev/null
    pkill -f "advancedqueue:queue:process dnd_ai" 2>/dev/null
    echo "Queue processor stopped."
  fi
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
