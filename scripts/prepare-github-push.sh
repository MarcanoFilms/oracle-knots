#!/usr/bin/env bash
# Prepare Oracle Knots repo for GitHub push via SSH (Arch Linux)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GITHUB_USER="${GITHUB_USER:-MarcanoFilms}"
GITHUB_REPO="${GITHUB_REPO:-oracle-knots}"
SSH_REMOTE="git@github.com:${GITHUB_USER}/${GITHUB_REPO}.git"

echo "==> Oracle Knots — GitHub SSH preparation"
echo "    Repo: $REPO_ROOT"
echo "    Remote: $SSH_REMOTE"
echo ""

# 1. SSH key check
if ! ssh -T -o BatchMode=yes -o ConnectTimeout=5 git@github.com 2>&1 | grep -qi "successfully authenticated\|Hi "; then
    echo "SSH to GitHub not configured yet. Run these steps:"
    echo ""
    echo "  # Generate key (if you don't have one)"
    echo "  ssh-keygen -t ed25519 -C \"your_email@example.com\" -f ~/.ssh/id_ed25519_github"
    echo ""
    echo "  # Add to ssh-agent"
    echo "  eval \"\$(ssh-agent -s)\""
    echo "  ssh-add ~/.ssh/id_ed25519_github"
    echo ""
    echo "  # Copy public key and add at https://github.com/settings/keys"
    echo "  cat ~/.ssh/id_ed25519_github.pub"
    echo ""
    echo "  # Optional ~/.ssh/config:"
    echo "  Host github.com"
    echo "    HostName github.com"
    echo "    User git"
    echo "    IdentityFile ~/.ssh/id_ed25519_github"
    echo ""
    read -r -p "Press Enter after SSH is configured, or Ctrl+C to abort..."
fi

# 2. Set SSH remote
if git remote get-url origin &>/dev/null; then
    git remote set-url origin "$SSH_REMOTE"
else
    git remote add origin "$SSH_REMOTE"
fi
echo "==> origin -> $(git remote get-url origin)"

# 3. Stage and commit if there are changes
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git status --short
    echo ""
    read -r -p "Commit all changes? [y/N] " ans
    if [[ "${ans,,}" == "y" ]]; then
        git commit -m "$(cat <<'EOF'
Oracle Knots Control Center: owl GUI, Sparrow wallet, CLI terminal

- Sovereign policy engine, Prometheus dashboard, BIP-110 status
- Wallet: UTXOs, coin control, PSBT, security, multi-wallet
- Oracle CLI terminal, owl-branded desktop launcher
- Portable paths, requirements.txt, GUI smoke tests, CI
EOF
)"
    fi
fi

# 4. Push
echo ""
echo "==> Ready to push. Run:"
echo "    git push -u origin main"
echo ""
read -r -p "Push now? [y/N] " push_ans
if [[ "${push_ans,,}" == "y" ]]; then
    git push -u origin main
    echo "Done: https://github.com/${GITHUB_USER}/${GITHUB_REPO}"
fi