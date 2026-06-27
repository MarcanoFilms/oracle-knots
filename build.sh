#!/usr/bin/env bash
# Build script for Oracle Knots

set -eo pipefail

echo "==> Configuring build for Oracle Knots..."
cmake -B build -DCMAKE_BUILD_TYPE=Release -DRDTS_CONSENT=IMPLICIT --toolchain /home/marcano/oracle-knots/depends/x86_64-pc-linux-gnu/toolchain.cmake

echo "==> Compiling Oracle Knots binaries..."
cmake --build build -j$(nproc)

echo "==> Build complete! Binaries are available in build/src/"
echo "To run the daemon: ./build/src/bitcoind"
echo "To use the CLI:   ./build/src/bitcoin-cli"
