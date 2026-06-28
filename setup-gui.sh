#!/usr/bin/env bash
# Set up Python virtual environment for Oracle Knots Control Center
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

if [ ! -d "gui-venv" ]; then
    python3 -m venv gui-venv
fi

./gui-venv/bin/pip install --upgrade pip
./gui-venv/bin/pip install -r requirements.txt

# pywebview on Linux often needs Qt backend
if ! ./gui-venv/bin/python -c "import webview" 2>/dev/null; then
    echo "Note: install Qt deps if pywebview fails — Arch: qt6-webengine"
fi

echo "GUI ready. Run: ./launch.sh"