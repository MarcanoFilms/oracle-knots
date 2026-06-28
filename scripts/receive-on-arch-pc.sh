#!/usr/bin/env bash
# Run this script ON THE OTHER Arch Linux PC (192.168.1.168) to download Oracle Knots
set -euo pipefail

SOURCE_IP="${1:-192.168.1.156}"
SOURCE_PORT="${2:-9876}"
ARCHIVE="oracle-knots-transfer.tar.gz"
DEST="${HOME}/oracle-knots"

echo "==> Downloading Oracle Knots from http://${SOURCE_IP}:${SOURCE_PORT}/"
curl -fL --progress-bar -o "/tmp/${ARCHIVE}" "http://${SOURCE_IP}:${SOURCE_PORT}/${ARCHIVE}"

echo "==> Extracting to ${DEST}"
mkdir -p "$(dirname "$DEST")"
rm -rf "${DEST}.bak"
[ -d "$DEST" ] && mv "$DEST" "${DEST}.bak"

tar xzf "/tmp/${ARCHIVE}" -C "$(dirname "$DEST")"
rm -f "/tmp/${ARCHIVE}"

cd "$DEST"
chmod +x launch.sh setup-gui.sh install-desktop.sh build.sh scripts/*.sh 2>/dev/null || true

echo ""
echo "==> Oracle Knots ready at: $DEST"
echo "    Next steps:"
echo "      cd $DEST"
echo "      ./setup-gui.sh          # GUI deps"
echo "      ./build.sh              # compile node (optional)"
echo "      ./install-desktop.sh    # owl desktop launcher"
echo "      ./scripts/prepare-github-push.sh   # push to GitHub via SSH"