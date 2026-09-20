#!/usr/bin/env bash
# Install Oracle Knots owl-themed desktop launcher (menu + desktop shortcut)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_SRC="$REPO_ROOT/oracle-knots.desktop"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_MENU="$APPS_DIR/oracle-knots.desktop"
DESKTOP_SHORTCUT="${XDG_DESKTOP_DIR:-$HOME/Desktop}/oracle-knots.desktop"

# Ensure PNG icon exists (some DEs handle PNG better than SVG)
if [ ! -f "$REPO_ROOT/gui/assets/oracle-owl-256.png" ]; then
    if command -v rsvg-convert >/dev/null 2>&1; then
        rsvg-convert -w 256 -h 256 "$REPO_ROOT/gui/assets/oracle-owl.svg" \
            -o "$REPO_ROOT/gui/assets/oracle-owl-256.png"
    else
        echo "Warning: rsvg-convert not found — install librsvg for PNG icon"
    fi
fi

install_entry() {
    local dest="$1"
    sed "s|@REPO_ROOT@|$REPO_ROOT|g" "$DESKTOP_SRC" > "$dest"
    chmod +x "$dest"
}

chmod +x "$REPO_ROOT/launch.sh"

mkdir -p "$APPS_DIR"
install_entry "$DESKTOP_MENU"

mkdir -p "$(dirname "$DESKTOP_SHORTCUT")"
install_entry "$DESKTOP_SHORTCUT"
chmod +x "$DESKTOP_SHORTCUT" 2>/dev/null || true

# Mark desktop shortcut as trusted (GNOME/KDE)
if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_SHORTCUT" metadata::trusted true 2>/dev/null || true
fi

update-desktop-database "$APPS_DIR" 2>/dev/null || true

echo "Oracle Knots owl launcher installed:"
echo "  Menu:    $DESKTOP_MENU"
echo "  Desktop: $DESKTOP_SHORTCUT"
echo "  Icon:    $REPO_ROOT/gui/assets/oracle-owl-256.png"
echo ""
echo "Search 'Oracle Knots' in your application menu."