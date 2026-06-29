#!/bin/bash
# Create GitHub release for Oracle Knots v1.0.0
# This script requires the 'gh' CLI to be installed
# Install from: https://cli.github.com/

set -e

VERSION="v1.0.0"
TITLE="Oracle Knots v1.0.0 - Official Launch"
NOTES_FILE="RELEASE_NOTES.md"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ Error: 'gh' CLI not found"
    echo ""
    echo "Install GitHub CLI from: https://cli.github.com/"
    echo ""
    echo "Then run: $0"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "$NOTES_FILE" ]; then
    echo "❌ Error: $NOTES_FILE not found"
    echo "Please run this script from the oracle-knots directory"
    exit 1
fi

echo "📦 Creating GitHub release..."
echo "Version: $VERSION"
echo "Title: $TITLE"
echo ""

# Create the release
gh release create "$VERSION" \
    --title "$TITLE" \
    --notes-file "$NOTES_FILE"

echo ""
echo "✅ Release created successfully!"
echo ""
echo "View the release at:"
echo "https://github.com/MarcanoFilms/oracle-knots/releases/tag/$VERSION"
