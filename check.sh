#!/usr/bin/env bash
#
# Run every mandatory quality gate for the Python engine.
#
# These are the gates AGENTS.md requires before any commit:
#   1. pylint  - 10.00/10, zero messages (rule 2/3)
#   2. mypy    - zero errors on src/ and tests/ (rule 6)
#   3. pyright - zero errors; same engine as VS Code Pylance (rule 3.1)
#   4. tests   - full suite green
#
# pyright is included because rule 3.1 requires Pylance to be happy. Without a
# terminal-runnable check, Pylance-only errors accumulate invisibly to anyone
# not looking at that exact file in the IDE.
#
# Usage:
#   ./check.sh          # run all gates
#   ./check.sh --fast   # skip the test suite (gates only)

set -uo pipefail

cd "$(dirname "$0")" || exit 1

PYTHON=".venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    echo "[ERROR] $PYTHON not found. Create the venv and install:"
    echo "        python3 -m venv .venv"
    echo "        .venv/bin/pip install -r requirements.txt -r requirements-dev.txt"
    exit 1
fi

FAILED=0

run_gate() {
    local name="$1"
    shift
    echo "======================================================================"
    echo "[GATE] $name"
    echo "======================================================================"
    if "$@"; then
        echo "[SUCCESS] $name passed"
    else
        echo "[FAILED] $name FAILED"
        FAILED=1
    fi
    echo
}

check_no_suppressions() {
    # AGENTS.md rules 2 and 6: fix the underlying issue, never silence the
    # checker. This gate exists because the rule was written down and violated
    # anyway - a documented rule that nothing enforces is not a rule.
    # Python sources only - the tests/*/README.md files quote these markers
    # while documenting the rule, and must not trip it.
    local hits
    hits=$(grep -rnE --include='*.py' --include='*.pyi' \
        '# *(type: *ignore|pylint: *disable|noqa|pragma)' \
        src/ tests/ stubs/ 2>/dev/null || true)
    local cfg
    cfg=$(grep -rn 'ignore_missing_imports' \
        mypy.ini pyrightconfig.json 2>/dev/null || true)

    if [ -n "$hits" ] || [ -n "$cfg" ]; then
        echo "Found checker suppressions - fix the underlying issue instead:"
        [ -n "$hits" ] && echo "$hits"
        [ -n "$cfg" ] && echo "$cfg"
        return 1
    fi
    echo "No type: ignore / pylint: disable / noqa / pragma found."
    return 0
}

check_script_exec_bits() {
    # This repo sets core.fileMode=false, so `chmod +x` is invisible to git and
    # a shell script can be committed as 100644. CI then fails with exit 126
    # ("Permission denied") - which is what happened to check.sh itself.
    # Fix a hit with: git update-index --chmod=+x <file>
    local bad
    bad=$(git ls-files -s -- '*.sh' 2>/dev/null | awk '$1 != "100755" {print $4}')

    if [ -n "$bad" ]; then
        echo "Shell scripts committed without the executable bit:"
        echo "$bad"
        echo "Fix with: git update-index --chmod=+x <file>"
        return 1
    fi
    echo "All committed shell scripts are executable."
    return 0
}

run_gate "shell scripts executable in git" check_script_exec_bits
run_gate "no checker suppressions" check_no_suppressions
run_gate "pylint (src/ tests/)" "$PYTHON" -m pylint src/ tests/
run_gate "mypy (src/)" "$PYTHON" -m mypy src/
run_gate "mypy (tests/)" "$PYTHON" -m mypy tests/
run_gate "pyright (Pylance parity)" "$PYTHON" -m pyright

if [ "${1:-}" != "--fast" ]; then
    run_gate "test suite" "$PYTHON" tests/run_all_tests.py
fi

echo "======================================================================"
if [ "$FAILED" -eq 0 ]; then
    echo "[SUCCESS] ALL GATES PASSED"
else
    echo "[FAILED] ONE OR MORE GATES FAILED - do not commit"
fi
echo "======================================================================"

exit "$FAILED"
