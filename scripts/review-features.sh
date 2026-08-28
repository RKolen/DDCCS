#!/usr/bin/env bash
#
# Summarise every feature worktree in one pass.
#
# Run this from the primary checkout when agents report they are done. It
# never checks anything out and never moves your HEAD - worktrees share one
# object store, so every branch is readable from here.
#
# Usage:
#   scripts/review-features.sh          # summary per worktree
#   scripts/review-features.sh --full   # complete diffstat, not truncated
#
# For one branch in detail:
#   git diff master...feature/ddcs-1
#   git -C ../ddcs-worktrees/ddcs-1 diff    # uncommitted work

set -uo pipefail

BASE_BRANCH="master"
MAX_STAT_LINES=12
FULL=0

case "${1:-}" in
    --full|-f) FULL=1 ;;
    "") ;;
    *) echo "Usage: scripts/review-features.sh [--full]" >&2; exit 1 ;;
esac

COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"
PRIMARY="$(dirname "$COMMON_DIR")"

found=0

# --porcelain emits a blank-line-separated record per worktree.
while IFS= read -r line; do
    case "$line" in
        "worktree "*) wt_path="${line#worktree }" ;;
        "branch "*)   wt_branch="${line#branch refs/heads/}" ;;
        "")
            [ "${wt_path:-}" = "$PRIMARY" ] && { wt_path=""; wt_branch=""; continue; }
            [ -z "${wt_branch:-}" ] && { wt_path=""; continue; }

            found=$((found + 1))

            # left-right counts: behind<TAB>ahead relative to the base.
            counts=$(git rev-list --left-right --count \
                "${BASE_BRANCH}...${wt_branch}" 2>/dev/null || echo "0	0")
            behind="${counts%%	*}"
            ahead="${counts##*	}"

            dirty=$(git -C "$wt_path" status --porcelain 2>/dev/null | wc -l)

            echo "======================================================================"
            echo "${wt_branch}"
            echo "  ${wt_path}"
            printf '  ahead %s, behind %s | uncommitted: %s file(s)\n' \
                "$ahead" "$behind" "$dirty"
            [ "$behind" != "0" ] && \
                echo "  [WARNING] behind ${BASE_BRANCH} - merge or rebase before review"
            [ "$dirty" != "0" ] && \
                echo "  [WARNING] uncommitted work - the diffstat below omits it"

            if [ "$ahead" = "0" ]; then
                echo "  (no commits yet)"
            else
                echo
                git --no-pager log --oneline "${BASE_BRANCH}..${wt_branch}" \
                    | sed 's/^/  /'
                echo
                stat=$(git --no-pager diff --stat \
                    "${BASE_BRANCH}...${wt_branch}")
                total=$(printf '%s\n' "$stat" | wc -l)
                if [ "$FULL" -eq 0 ] && [ "$total" -gt "$MAX_STAT_LINES" ]; then
                    printf '%s\n' "$stat" | head -n "$MAX_STAT_LINES" \
                        | sed 's/^/  /'
                    echo "  ... $((total - MAX_STAT_LINES)) more (use --full)"
                else
                    printf '%s\n' "$stat" | sed 's/^/  /'
                fi
            fi
            echo
            wt_path=""; wt_branch=""
            ;;
    esac
done < <(git worktree list --porcelain; echo)

if [ "$found" -eq 0 ]; then
    echo "No feature worktrees. Create one with scripts/new-feature.sh"
fi
