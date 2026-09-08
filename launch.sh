#!/usr/bin/env bash
# Oracle Knots Control Center — The Oracle watches the chain
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

# WebKitGTK (pywebview) crashea bajo Wayland+NVIDIA con "Error 71 (Protocol error)".
# Ruta la ventana por XWayland y desactiva el renderer DMABUF de WebKit (roto en NVIDIA).
export GDK_BACKEND="${GDK_BACKEND:-x11}"
export WEBKIT_DISABLE_DMABUF_RENDERER="${WEBKIT_DISABLE_DMABUF_RENDERER:-1}"
export WEBKIT_DISABLE_COMPOSITING_MODE="${WEBKIT_DISABLE_COMPOSITING_MODE:-1}"

if [ ! -d "gui-venv" ]; then
    echo "Oracle Knots: setting up GUI environment..."
    ./setup-gui.sh
fi

if [ ! -f "gui-venv/bin/python" ]; then
    echo "Error: gui-venv not found. Run: ./setup-gui.sh"
    exit 1
fi

exec ./gui-venv/bin/python gui.py