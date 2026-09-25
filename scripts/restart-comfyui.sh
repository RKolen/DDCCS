#!/usr/bin/env bash
# Restart the ComfyUI this host started, and wait for it to answer.
#
# ComfyUI does not give system RAM back. /free unloads models from the GPU but
# the process keeps the arena it grew loading them, so the second scene render
# of a session starts with no room and the kernel takes the process out
# mid-render. Restarting is the only thing that returns the memory.
#
# Processes are found by command line, never by what is listening on a port.
# A port tells you nothing about what you are about to stop, and killing
# whatever held one has taken down a browser on this machine before.
#
# Reads the same variables start.sh uses, so the ComfyUI that comes back is
# the one the deployment started with.
set -uo pipefail

: "${COMFYUI_DIR:?set COMFYUI_DIR to the ComfyUI install path}"
: "${COMFYUI_PORT:?set COMFYUI_PORT}"
: "${COMFYUI_HOST:?set COMFYUI_HOST}"
COMFYUI_EXTRA_ARGS="${COMFYUI_EXTRA_ARGS:-}"
COMFYUI_LOG_FILE="${COMFYUI_LOG_FILE:-$COMFYUI_DIR/.comfyui.log}"
COMFYUI_RESTART_TIMEOUT="${COMFYUI_RESTART_TIMEOUT:-240}"

ROOT=$(cd "$COMFYUI_DIR" && pwd)
HEALTH="http://$COMFYUI_HOST:$COMFYUI_PORT/system_stats"

# Only processes whose command line names THIS install's main.py. Read into
# an array rather than a string: unquoted expansion to split a PID list is
# exactly what shellcheck warns about, and an array says what is meant.
comfyui_pids() {
  local found=() pid line
  mapfile -t found < <(pgrep -f -- "$ROOT.*main\.py" 2>/dev/null || true)
  for pid in "${found[@]}"; do
    [[ -z "$pid" || "$pid" == "$$" || "$pid" == "$PPID" ]] && continue
    # Read the command line back. pgrep matched a pattern; this confirms the
    # process really is this install's entry point before we signal it.
    line=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)
    [[ "$line" == *"$ROOT"* && "$line" == *main.py* ]] && printf '%s\n' "$pid"
  done
}

read_pids() {
  local -n out=$1
  out=()
  local pid
  while read -r pid; do
    [[ -n "$pid" ]] && out+=("$pid")
  done < <(comfyui_pids)
}

read_pids PIDS
if (( ${#PIDS[@]} > 0 )); then
  echo "Stopping ComfyUI: ${PIDS[*]}"
  kill "${PIDS[@]}" 2>/dev/null || true
  for _ in $(seq 1 20); do
    read_pids LEFT
    (( ${#LEFT[@]} == 0 )) && break
    sleep 1
  done
  read_pids LEFT
  if (( ${#LEFT[@]} > 0 )); then
    echo "SIGTERM ignored, sending SIGKILL: ${LEFT[*]}"
    kill -9 "${LEFT[@]}" 2>/dev/null || true
    sleep 1
  fi
fi

PYTHON="$ROOT/venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="python3"
ARGS=()
[[ -n "$COMFYUI_EXTRA_ARGS" ]] && read -ra ARGS <<< "$COMFYUI_EXTRA_ARGS"

( cd "$ROOT" && exec "$PYTHON" main.py --port "$COMFYUI_PORT" "${ARGS[@]}" ) \
  >> "$COMFYUI_LOG_FILE" 2>&1 &
echo "ComfyUI PID: $! (logs: $COMFYUI_LOG_FILE)"

for _ in $(seq 1 "$COMFYUI_RESTART_TIMEOUT"); do
  if curl -sf --max-time 2 "$HEALTH" >/dev/null 2>&1; then
    echo "ComfyUI is ready on :$COMFYUI_PORT"
    exit 0
  fi
  sleep 1
done

echo "ComfyUI did not answer $HEALTH within ${COMFYUI_RESTART_TIMEOUT}s" >&2
exit 1
