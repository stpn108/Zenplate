#!/bin/bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = "main" ]; then
    echo "Already on main, nothing to do."
    exit 0
fi

echo "Merge ${BRANCH} → main"
git switch main && git merge "$BRANCH" && git push || exit 1

echo "Waiting for version-bump (GitHub Action)..."
sleep 15
git pull origin main
echo "Version: $(cat VERSION)"

# Fast-forward feature branch to main (including version bump)
git branch -f "$BRANCH" main
git switch $BRANCH
git push
echo "Branch '${BRANCH}' updated to main and pushed."
