#!/bin/bash
set -e

RETURN_TO_BRANCH=0
for arg in "$@"; do
    case "$arg" in
        --return)
            RETURN_TO_BRANCH=1
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Usage: $0 [--return]" >&2
            exit 2
            ;;
    esac
done

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = "main" ]; then
    echo "Already on main, nothing to do."
    exit 0
fi

echo "Merge ${BRANCH} → main"

git switch main

# Sync local main with origin BEFORE attempting the merge so a moving
# remote (e.g. version-bump from a previous merge) doesn't cause the push
# to be rejected as non-fast-forward. Untracked files in working tree
# directories that git wants to populate (e.g. bot/qa_reports/ written by
# the in-container QA runner) would block the implicit checkout, so stash
# them out of the way and restore afterwards.
STASHED=""
if ! git pull --ff-only origin main 2>/dev/null; then
    if [ -n "$(git ls-files --others --exclude-standard)" ]; then
        echo "Stashing untracked files to allow main checkout..."
        git stash push --include-untracked --message "merge-to-main: temp untracked stash" >/dev/null
        STASHED="yes"
    fi
    git pull --ff-only origin main
fi

git merge "$BRANCH"
git push

echo "Waiting for version-bump (GitHub Action)..."
sleep 15
git pull origin main
echo "Version: $(cat VERSION)"

# Fast-forward feature branch to main (including version bump) so the
# remote feature branch reflects the merged state regardless of whether
# we switch back to it.
git branch -f "$BRANCH" main
git push origin "$BRANCH"

if [ "$RETURN_TO_BRANCH" -eq 1 ]; then
    git switch "$BRANCH"
    if [ "$STASHED" = "yes" ]; then
        echo "Restoring stashed untracked files..."
        git stash pop >/dev/null || echo "Stash pop conflict — review with 'git stash list'."
    fi
    echo "Branch '${BRANCH}' updated to main and pushed. Returned to '${BRANCH}'."
else
    if [ "$STASHED" = "yes" ]; then
        echo "Restoring stashed untracked files on main..."
        git stash pop >/dev/null || echo "Stash pop conflict — review with 'git stash list'."
    fi
    echo "Branch '${BRANCH}' updated to main and pushed. Staying on 'main'."
fi
