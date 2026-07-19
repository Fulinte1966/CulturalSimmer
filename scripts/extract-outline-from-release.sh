#!/usr/bin/env bash
set -euo pipefail

# Extract PDF outline from a GitHub Release and save as JSON.
# Usage: ./scripts/extract-outline-from-release.sh <id> <edition>
# Example: ./scripts/extract-outline-from-release.sh A9-1 1

if [ $# -ne 2 ]; then
  echo "Usage: $0 <id> <edition>"
  echo "Example: $0 A9-1 1"
  exit 1
fi

ID="$1"
EDITION="$2"
TAG="${ID}_v${EDITION}"
PDF="${TAG}.pdf"

if ! command -v gh &>/dev/null; then
  echo "Error: GitHub CLI (gh) is not installed."
  echo "Install it from: https://cli.github.com/"
  exit 1
fi

echo "Downloading ${PDF} from release ${TAG}..."

mkdir -p .cache/pdfs

if ! gh release download "$TAG" \
  --repo Fulinte1966/CulturalSimmer \
  --pattern "$PDF" \
  --dir ".cache/pdfs" \
  --clobber; then
  echo "Error: Failed to download ${PDF} from release ${TAG}"
  exit 1
fi

echo "Extracting cover, outline, and reading metadata..."

python scripts/extract-book-assets.py ".cache/pdfs/$PDF" "$ID" "$EDITION"

echo "Done."
echo "Remember to commit the generated cover, outline, and reading files."
