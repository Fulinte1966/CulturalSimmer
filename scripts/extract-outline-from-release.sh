#!/usr/bin/env bash
set -euo pipefail

# Extract PDF outline from a GitHub Release and save as JSON.
# Usage: ./scripts/extract-outline-from-release.sh <id> <edition>
# Example: ./scripts/extract-outline-from-release.sh A12-8-2 1

if [ $# -ne 2 ]; then
  echo "Usage: $0 <id> <edition>"
  echo "Example: $0 A12-8-2 1"
  exit 1
fi

ID="$1"
EDITION="$2"
TAG="${ID}_v${EDITION}"
PDF="${TAG}.pdf"
OUT="src/data/outlines/${TAG}.json"

if ! command -v gh &>/dev/null; then
  echo "Error: GitHub CLI (gh) is not installed."
  echo "Install it from: https://cli.github.com/"
  exit 1
fi

echo "Downloading ${PDF} from release ${TAG}..."

mkdir -p .cache/pdfs

if ! gh release download "$TAG" \
  --repo poyinte/ebook-library \
  --pattern "$PDF" \
  --dir ".cache/pdfs" \
  --clobber; then
  echo "Error: Failed to download ${PDF} from release ${TAG}"
  exit 1
fi

echo "Extracting outline..."

python scripts/extract-outline.py ".cache/pdfs/$PDF" "$OUT"

echo "Done: ${OUT}"
echo "Remember to commit this file to the repository."
