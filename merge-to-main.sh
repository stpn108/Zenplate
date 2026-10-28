#!/bin/bash
set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = "main" ]; then
    echo "Already on main, nothing to do."
    exit 0
fi

# T-010: a merge left half-finished by an earlier run makes everything below
# behave unpredictably (the `git switch main` fails, and a later `git push`
# publishes whatever else is on main instead of the merge). Refuse to start.
if [ -e "$(git rev-parse --git-dir)/MERGE_HEAD" ]; then
    echo "A merge is already in progress. Finish or abandon it first:"
    echo "  git merge --abort      # discard it"
    echo "  git status             # or resolve, git add <files>, git commit"
    exit 1
fi

echo "Merge ${BRANCH} → main"

git switch main

# Sync local main with origin BEFORE attempting the merge so a moving
# remote (e.g. the version bump from a previous merge) doesn't cause the push
# to be rejected as non-fast-forward. Untracked files in working tree
# directories that git wants to populate would block the implicit checkout,
# so stash them out of the way and restore afterwards.
STASHED=""
if ! git pull --ff-only origin main 2>/dev/null; then
    if [ -n "$(git ls-files --others --exclude-standard)" ]; then
        echo "Stashing untracked files to allow main checkout..."
        git stash push --include-untracked --message "merge-to-main: temp untracked stash" >/dev/null
        STASHED="yes"
    fi
    git pull --ff-only origin main
fi

# T-010: the dry run below merges and aborts, which is only safe on a clean
# tree — an abort would otherwise take uncommitted work with it.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "Uncommitted changes present. Commit or stash them first:"
    git status --short --untracked-files=no | sed 's/^/  /'
    exit 1
fi

# T-010: refuse to start a merge that would strand the repo. Without this,
# conflicting files made `set -e` abort mid-merge, leaving the working tree in
# MERGING with no instructions, and the next `git push` published something
# other than the merge.
if ! git merge --no-commit --no-ff "$BRANCH" >/dev/null 2>&1; then
    CONFLICTS=$(git diff --name-only --diff-filter=U)
    git merge --abort 2>/dev/null || true
    echo ""
    echo "ABORTED: '${BRANCH}' does not merge cleanly into main."
    echo "The working tree is untouched — nothing is half-merged."
    echo ""
    echo "Conflicting files:"
    echo "$CONFLICTS" | sed 's/^/  /'
    echo ""
    echo "Usually main holds an older COPY of these files from a previous"
    echo "merge, and the branch is simply newer. Check before trusting that:"
    echo "  git diff main..${BRANCH} -- <file>"
    echo ""
    echo "If the branch is the newer side, resolve by taking it:"
    echo "  git merge ${BRANCH}"
    echo "  git checkout ${BRANCH} -- <file> [<file> ...]"
    echo "  git add <file> [<file> ...]      # name them; -A sweeps up stray work"
    echo "  git commit --no-edit && git push origin main"
    exit 1
fi
git merge --abort 2>/dev/null || git reset --hard HEAD --quiet

git merge "$BRANCH"
git push

echo "Waiting for version-bump (GitHub Action)..."
sleep 15
git pull origin main
echo "Version: $(cat VERSION)"

# Fast-forward feature branch to main (including version bump).
git branch -f "$BRANCH" main
git switch "$BRANCH"

if [ "$STASHED" = "yes" ]; then
    echo "Restoring stashed untracked files..."
    git stash pop >/dev/null || echo "Stash pop conflict — review with 'git stash list'."
fi

git push
echo "Branch '${BRANCH}' updated to main and pushed."
