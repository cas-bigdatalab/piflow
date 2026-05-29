#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
RELEASE_ROOT="$PROJECT_ROOT/release"
STAGE_DIR="$RELEASE_ROOT/$PROJECT_NAME"
ARCHIVE_BASENAME="${PROJECT_NAME}-release"
TAR_PATH="$PROJECT_ROOT/${ARCHIVE_BASENAME}.tar.gz"
ZIP_PATH="$PROJECT_ROOT/${ARCHIVE_BASENAME}.zip"

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required but not installed." >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "zip is required but not installed." >&2
  exit 1
fi

echo "Packaging release for: $PROJECT_NAME"
echo "Project root: $PROJECT_ROOT"

rm -rf "$STAGE_DIR"
mkdir -p "$RELEASE_ROOT"

RSYNC_EXCLUDES=(
  --exclude ".git"
  --exclude ".idea"
  --exclude ".pytest_cache"
  --exclude ".DS_Store"
  --exclude "__pycache__"
  --exclude "*.pyc"
  --exclude "*.pyo"
  --exclude "*.log"
  --exclude "release"
  --exclude "flow-deepagents-0408-release.tar.gz"
  --exclude "flow-deepagents-0408-release.zip"
  --exclude "vue-web/node_modules"
  --exclude "vue-web/.vite"
  --exclude "workspace/temp"
  --exclude "workspace/outputs"
  --exclude "workspace/artifacts"
  --exclude "workspace/process_*"
)

rsync -a "${RSYNC_EXCLUDES[@]}" "$PROJECT_ROOT/" "$STAGE_DIR/"

rm -f "$TAR_PATH" "$ZIP_PATH"

tar -czf "$TAR_PATH" -C "$RELEASE_ROOT" "$PROJECT_NAME"
(
  cd "$RELEASE_ROOT"
  zip -rq "$ZIP_PATH" "$PROJECT_NAME"
)

echo "Release staging directory: $STAGE_DIR"
echo "Created: $TAR_PATH"
echo "Created: $ZIP_PATH"
