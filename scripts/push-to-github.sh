#!/usr/bin/env bash
# Non-interactive GitHub push — no build, no GUI, no node required
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GITHUB_USER="${GITHUB_USER:-MarcanoFilms}"
GITHUB_REPO="${GITHUB_REPO:-oracle-knots}"
SSH_REMOTE="git@github.com:${GITHUB_USER}/${GITHUB_REPO}.git"
BRANCH="${BRANCH:-main}"

echo "==> Oracle Knots — push to GitHub (git only)"
echo "    Repo:   $REPO_ROOT"
echo "    Remote: $SSH_REMOTE"
echo "    Branch: $BRANCH"
echo ""

if ! git rev-parse --git-dir &>/dev/null; then
    echo "ERROR: No .git directory. Re-transfer the repo with git history included."
    exit 1
fi

if ! ssh -T -o BatchMode=yes -o ConnectTimeout=10 git@github.com 2>&1 | grep -qi "successfully authenticated\|Hi "; then
    echo "ERROR: SSH to GitHub not configured. See GITHUB_PUSH.md"
    exit 1
fi

git remote remove dathonohm 2>/dev/null || true

if git remote get-url origin &>/dev/null; then
    git remote set-url origin "$SSH_REMOTE"
else
    git remote add origin "$SSH_REMOTE"
fi

if git status --porcelain | grep -q '^.D depends/'; then
    echo "==> Restoring deleted depends/ files (tarball transfer artifact)"
    git restore depends/
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "WARNING: Uncommitted changes remain:"
    git status --short
    echo ""
    echo "Commit or stash before pushing. Aborting."
    exit 1
fi

echo "==> Pushing $BRANCH to origin..."
git push -u origin "$BRANCH"
echo ""
echo "Done: https://github.com/${GITHUB_USER}/${GITHUB_REPO}"