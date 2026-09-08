#!/usr/bin/env bash
# Oracle Knots Control Center — The Oracle watches the chain
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

if [ ! -d "gui-venv" ]; then
    echo "Oracle Knots: setting up GUI environment..."
    ./setup-gui.sh
fi

if [ ! -f "gui-venv/bin/python" ]; then
    echo "Error: gui-venv not found. Run: ./setup-gui.sh"
    exit 1
fi

exec ./gui-venv/bin/python gui.py