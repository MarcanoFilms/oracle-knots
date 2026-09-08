#!/usr/bin/env bash
# Build script for Oracle Knots

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

TOOLCHAIN="$REPO_ROOT/depends/x86_64-pc-linux-gnu/toolchain.cmake"
# RDTS_CONSENT is required by the Knots BIP-110 gate on every build (with or
# without the depends toolchain), so it must always be passed.
CMAKE_EXTRA=(-DRDTS_CONSENT=IMPLICIT)

if [ -f "$TOOLCHAIN" ]; then
    CMAKE_EXTRA+=(--toolchain "$TOOLCHAIN")
    echo "==> Using depends toolchain"
else
    echo "==> Building without depends toolchain (system libs)"
fi

echo "==> Configuring build for Oracle Knots..."
cmake -B build -DCMAKE_BUILD_TYPE=Release "${CMAKE_EXTRA[@]}"

echo "==> Compiling Oracle Knots binaries..."
cmake --build build -j"$(nproc)"

BIN_DIR="build/bin"
if [ ! -d "$BIN_DIR" ]; then
    BIN_DIR="build/src"
fi

echo "==> Node build complete! Binaries are in $BIN_DIR/"
echo "  Daemon: $BIN_DIR/bitcoind"
echo "  CLI:    $BIN_DIR/bitcoin-cli"

# ---------------------------------------------------------------------------
# All-in-one: also build the DATUM Gateway (CONVOY) if vendored, unless
# --node-only is passed. Skips gracefully if the submodule or its deps are
# missing so a node-only build still succeeds.
# ---------------------------------------------------------------------------
NODE_ONLY=0
for a in "$@"; do [ "$a" = "--node-only" ] && NODE_ONLY=1; done

DATUM_DIR="$REPO_ROOT/mining/datum-convoy"
if [ "$NODE_ONLY" = 0 ] && [ -f "$DATUM_DIR/CMakeLists.txt" ]; then
    echo ""
    echo "==> Building DATUM Gateway (CONVOY) for sovereign mining..."
    missing=""
    for lib in libcurl jansson libmicrohttpd libsodium; do
        pkg-config --exists "$lib" 2>/dev/null || missing="$missing $lib"
    done
    if [ -n "$missing" ]; then
        echo "  !! Skipping DATUM build — missing dev libs:$missing"
        echo "     Arch: sudo pacman -S curl jansson libmicrohttpd libsodium"
        echo "     Deb:  sudo apt install libcurl4-openssl-dev libjansson-dev libmicrohttpd-dev libsodium-dev"
    else
        cmake -S "$DATUM_DIR" -B "$DATUM_DIR/build" -DCMAKE_BUILD_TYPE=Release
        cmake --build "$DATUM_DIR/build" -j"$(nproc)"
        echo "  DATUM Gateway: $DATUM_DIR/build/datum_gateway"
    fi
elif [ "$NODE_ONLY" = 0 ]; then
    echo ""
    echo "==> DATUM Gateway not vendored (mining/datum-convoy missing)."
    echo "    Run:  git submodule update --init --recursive"
fi

echo ""
echo "==> Done. Launch the all-in-one stack with:  ./oracle-knots"