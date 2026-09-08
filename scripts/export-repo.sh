#!/usr/bin/env bash
# Export Oracle Knots repo as tarball (excludes build, venv, git objects)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$HOME}"
STAMP=$(date +%Y%m%d)
ARCHIVE="$OUT_DIR/oracle-knots-${STAMP}.tar.gz"

cd "$(dirname "$REPO_ROOT")"
tar czf "$ARCHIVE" \
    --exclude='oracle-knots/.git' \
    --exclude='oracle-knots/gui-venv' \
    --exclude='oracle-knots/build' \
    --exclude='oracle-knots/depends/work' \
    --exclude='oracle-knots/depends/built' \
    oracle-knots

echo "Exported: $ARCHIVE"
echo "Size: $(du -h "$ARCHIVE" | cut -f1)"