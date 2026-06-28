#!/usr/bin/env bash
# Build script for Oracle Knots

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

TOOLCHAIN="$REPO_ROOT/depends/x86_64-pc-linux-gnu/toolchain.cmake"
CMAKE_EXTRA=()

if [ -f "$TOOLCHAIN" ]; then
    CMAKE_EXTRA=(--toolchain "$TOOLCHAIN" -DRDTS_CONSENT=IMPLICIT)
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

echo "==> Build complete! Binaries are in $BIN_DIR/"
echo "  Daemon: $BIN_DIR/bitcoind"
echo "  CLI:    $BIN_DIR/bitcoin-cli"