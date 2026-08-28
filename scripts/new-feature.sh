#!/usr/bin/env bash
#
# Create an isolated git worktree for one feature.
#
# Two agents working in the same checkout overwrite each other's edits and
# each other's ./check.sh runs. A worktree gives every agent its own working
# directory and branch on top of the same object store - no second clone, no
# rebasing to test.
#
# Branches are numbered: feature/ddcs-1, feature/ddcs-2, ... The next free
# number is taken from local branches, remote branches, and existing worktree
# directories, so it never collides with a branch someone already pushed.
#
# The untracked things a fresh worktree does not get - .venv, .env,
# game_data, frontend/node_modules - are symlinked back to the primary
# checkout. ./check.sh needs .venv/bin/python and will not run without it.
#
# Usage:
#   scripts/new-feature.sh          # next free number
#   scripts/new-feature.sh 7        # force feature/ddcs-7
#
# Environment:
#   DDCS_WORKTREE_HOME   where worktrees live
#                        (default: <parent of repo>/ddcs-worktrees)
#
# Remove one when the branch is merged:
#   git worktree remove ../ddcs-worktrees/ddcs-1
#   git branch -d feature/ddcs-1

set -euo pipefail

BASE_BRANCH="master"
SHARED_PATHS=(".venv" ".env" "game_data" "frontend/node_modules")

# Resolve the primary checkout even when this script is run from a worktree:
# --git-common-dir always points at the primary .git directory.
COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"
PRIMARY="$(dirname "$COMMON_DIR")"
WORKTREE_HOME="${DDCS_WORKTREE_HOME:-$(dirname "$PRIMARY")/ddcs-worktrees}"

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

# Highest feature/ddcs-<n> already spoken for, across branches and directories.
highest_used() {
    {
        git for-each-ref --format='%(refname:short)' refs/heads refs/remotes \
            | sed -n 's#^\(.*/\)\?feature/ddcs-\([0-9]\{1,\}\)$#\2#p'
        ls -1 "$WORKTREE_HOME" 2>/dev/null \
            | sed -n 's#^ddcs-\([0-9]\{1,\}\)$#\1#p'
        echo 0
    } | sort -n | tail -1
}

if [ $# -gt 1 ]; then
    die "Usage: scripts/new-feature.sh [number]"
fi

if [ $# -eq 1 ]; then
    case "$1" in
        ''|*[!0-9]*) die "Number must be a positive integer, got: $1" ;;
    esac
    NUMBER="$1"
else
    NUMBER=$(( $(highest_used) + 1 ))
fi

BRANCH="feature/ddcs-${NUMBER}"
TARGET="${WORKTREE_HOME}/ddcs-${NUMBER}"

if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
    die "Branch ${BRANCH} already exists. Pick another number."
fi
if [ -e "$TARGET" ]; then
    die "${TARGET} already exists. Remove it or pick another number."
fi
if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
    die "Base branch ${BASE_BRANCH} not found."
fi

# Branching off a stale master means the agent starts behind. Say so rather
# than fetching - the network is not this script's business.
if git rev-parse --verify --quiet "refs/remotes/origin/${BASE_BRANCH}" >/dev/null
then
    BEHIND=$(git rev-list --count \
        "${BASE_BRANCH}..origin/${BASE_BRANCH}" 2>/dev/null || echo 0)
    if [ "$BEHIND" != "0" ]; then
        echo "[WARNING] ${BASE_BRANCH} is ${BEHIND} commit(s) behind" \
             "origin/${BASE_BRANCH}. Consider: git pull --ff-only"
    fi
fi

# Uncommitted work stays behind in whichever checkout it was made in. That is
# usually what you want, but it is worth saying out loud before branching.
if [ -n "$(git -C "$PRIMARY" status --porcelain)" ]; then
    echo "[WARNING] The primary checkout has uncommitted changes."
    echo "          They stay there - ${BRANCH} branches from" \
         "${BASE_BRANCH} as committed."
fi

mkdir -p "$WORKTREE_HOME"
git worktree add "$TARGET" -b "$BRANCH" "$BASE_BRANCH"

echo
for rel in "${SHARED_PATHS[@]}"; do
    src="${PRIMARY}/${rel}"
    dst="${TARGET}/${rel}"
    if [ ! -e "$src" ]; then
        echo "[SKIP]  ${rel} - not present in the primary checkout"
        continue
    fi
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        echo "[SKIP]  ${rel} - already present in the worktree"
        continue
    fi
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
    echo "[LINK]  ${rel} -> ${src}"
done

cat <<EOF

======================================================================
[SUCCESS] ${BRANCH}
======================================================================
  cd ${TARGET}
  ./check.sh --fast

Shared, NOT isolated by this worktree - claim before use:
  - DDEV / Drupal (one database, one router port for the whole machine)
  - Gatsby dev server (set GATSBY_PORT, or only one agent runs develop)
  - Ollama, Milvus, ComfyUI (single instances, CPU inference)
  - frontend/node_modules is a symlink: npm install mutates it for everyone

When the branch is merged:
  git worktree remove ${TARGET}
  git branch -d ${BRANCH}
EOF
