#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MACOS_ROOT="$ROOT/macos"
DEST="${PLEX_CURATOR_MAC_APP_DEST:-$HOME/Applications/Plex Curator.app}"
CONFIG_DIR="$HOME/.config/plex-curator"
BACKUP_ROOT="$CONFIG_DIR/deployment-backups"
DRY_RUN=0
OPEN_APP=1

usage() {
  cat <<'EOF'
Usage: ./scripts/install-macos-app.sh [--dry-run] [--no-open]

Builds the SwiftUI client and installs it to:
  ~/Applications/Plex Curator.app

An existing app is backed up before replacement.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --no-open) OPEN_APP=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

[[ -f "$MACOS_ROOT/Package.swift" ]] || {
  echo "Missing macOS Package.swift" >&2
  exit 1
}

echo "Plex Curator macOS app deployment"
echo "Source: $MACOS_ROOT"
echo "Target: $DEST"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo
  echo "DRY RUN — no files will be changed."
  echo "Would build the release SwiftUI app."
  if [[ -d "$DEST" ]]; then
    echo "Would back up existing app to: $BACKUP_ROOT/<timestamp>/Plex Curator.app"
  fi
  echo "Would install the new app to: $DEST"
  [[ "$OPEN_APP" -eq 1 ]] && echo "Would open the installed app."
  exit 0
fi

[[ "$(uname -s)" == "Darwin" ]] || {
  echo "The macOS app can only be built/installed on macOS." >&2
  exit 1
}

command -v swift >/dev/null 2>&1 || {
  echo "Swift toolchain not found. Install Xcode Command Line Tools or Xcode." >&2
  exit 1
}

mkdir -p "$CONFIG_DIR" "$BACKUP_ROOT" "$(dirname "$DEST")"
chmod 700 "$CONFIG_DIR" 2>/dev/null || true

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

if [[ -d "$DEST" ]]; then
  mkdir -p "$BACKUP_DIR"
  echo "Backing up current macOS app..."
  /usr/bin/ditto "$DEST" "$BACKUP_DIR/Plex Curator.app"
fi

bash "$MACOS_ROOT/scripts/build-app.sh"

SOURCE_APP="$MACOS_ROOT/dist/Plex Curator.app"
[[ -d "$SOURCE_APP" ]] || {
  echo "Build completed but app bundle was not found: $SOURCE_APP" >&2
  exit 1
}

rm -rf "$DEST"
/usr/bin/ditto "$SOURCE_APP" "$DEST"

echo "Installed: $DEST"

if [[ "$OPEN_APP" -eq 1 ]]; then
  open "$DEST"
fi
