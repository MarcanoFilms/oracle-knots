#!/usr/bin/env bash
# Install and enable Tor + i2pd for Oracle Knots P2P privacy networks.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BITCOIN_CONF="${BITCOIN_CONF:-$HOME/.bitcoin/bitcoin.conf}"

echo "==> Oracle Knots — Tor & I2P setup"

if command -v pacman >/dev/null 2>&1; then
    echo "Installing tor and i2pd (Arch)..."
    sudo pacman -S --needed --noconfirm tor i2pd
elif command -v apt-get >/dev/null 2>&1; then
    echo "Installing tor and i2pd (Debian/Ubuntu)..."
    sudo apt-get update
    sudo apt-get install -y tor i2pd
else
    echo "Install tor and i2pd manually for your distro, then re-run this script."
    exit 1
fi

echo "==> Configuring Tor control port (listenonion / hidden service)..."
sudo mkdir -p /etc/tor/torrc.d
sudo cp "$REPO_ROOT/scripts/tor-bitcoind.conf" /etc/tor/torrc.d/50-bitcoind.conf
if ! grep -q '%include /etc/tor/torrc.d' /etc/tor/torrc 2>/dev/null; then
    if grep -q '#%include /etc/torrc.d' /etc/tor/torrc 2>/dev/null; then
        sudo sed -i 's|#%include /etc/torrc.d/\*.conf|%include /etc/tor/torrc.d/*.conf|' /etc/tor/torrc
    else
        echo '%include /etc/tor/torrc.d/*.conf' | sudo tee -a /etc/tor/torrc >/dev/null
    fi
fi
sudo tor -f /etc/tor/torrc --verify-config

echo "==> Enabling services..."
sudo systemctl enable --now tor
sudo systemctl enable --now i2pd

echo "==> Waiting for SOCKS/SAM ports..."
for i in $(seq 1 30); do
    if ss -tln 2>/dev/null | grep -qE ':9050 |:7656 ' || \
       netstat -tln 2>/dev/null | grep -qE ':9050 |:7656 '; then
        break
    fi
    sleep 1
done

echo ""
echo "Listening ports:"
ss -tln 2>/dev/null | grep -E ':9050|:9051|:7656' || \
    netstat -tln 2>/dev/null | grep -E ':9050|:9051|:7656' || \
    echo "  (could not verify — check: systemctl status tor i2pd)"

if [[ -f "$BITCOIN_CONF" ]]; then
    echo ""
    echo "bitcoin.conf already at: $BITCOIN_CONF"
    echo "Expected entries:"
    grep -E '^(onion|torcontrol|i2psam|listenonion|i2pacceptincoming)=' "$BITCOIN_CONF" 2>/dev/null || true
else
    echo "Warning: $BITCOIN_CONF not found"
fi

echo ""
echo "Restart bitcoind to apply network settings:"
echo "  $REPO_ROOT/build/bin/bitcoin-cli stop"
echo "  # then Start Node from the Control Center"
echo ""
echo "Verify peers: bitcoin-cli -addrinfo | jq '.networks'"