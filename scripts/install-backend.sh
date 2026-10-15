#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/backend"
TARGET="${PLEX_CURATOR_TARGET:-/Applications/PlexCurator}"
CONFIG_DIR="$HOME/.config/plex-curator"
BACKUP_ROOT="$CONFIG_DIR/deployment-backups"
DRY_RUN=0
RESTART_API=1

usage() {
  cat <<'EOF'
Usage: ./scripts/install-backend.sh [--dry-run] [--no-restart-api] [--target PATH]

Safely installs/updates the backend while preserving:
  ~/.config/plex-curator/
  existing .venv/ when present

The current live application directory is backed up before deployment.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --no-restart-api) RESTART_API=0; shift ;;
    --target)
      [[ $# -ge 2 ]] || { echo "--target requires a path" >&2; exit 2; }
      TARGET="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

required=(
  "$SOURCE/plex_curator.py"
  "$SOURCE/plex_curator_api.py"
  "$SOURCE/plex-curator"
  "$SOURCE/plex-curator-api"
  "$SOURCE/launchd-manager.py"
  "$SOURCE/requirements.txt"
  "$SOURCE/install.sh"
)

for path in "${required[@]}"; do
  [[ -e "$path" ]] || { echo "Missing required source file: $path" >&2; exit 1; }
done

echo "Plex Curator backend deployment"
echo "Source:  $SOURCE"
echo "Target:  $TARGET"
echo "Config:  $CONFIG_DIR"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo
  echo "DRY RUN — no files will be changed."
  if [[ -d "$TARGET" ]]; then
    echo "Would back up existing target to: $BACKUP_ROOT/<timestamp>/PlexCurator"
  else
    echo "No existing target detected."
  fi
  echo "Would rsync backend source into target, preserving target/.venv/"
  echo "Would run target/install.sh"
  echo "Would run Doctor when $CONFIG_DIR/.env exists"
  if [[ "$RESTART_API" -eq 1 ]]; then
    echo "Would reload api-server LaunchAgent if its plist already exists"
  fi
  exit 0
fi

[[ "$(uname -s)" == "Darwin" ]] || {
  echo "Actual deployment is supported on macOS only. Use --dry-run elsewhere." >&2
  exit 1
}

mkdir -p "$CONFIG_DIR" "$BACKUP_ROOT"
chmod 700 "$CONFIG_DIR" 2>/dev/null || true

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

if [[ -d "$TARGET" ]]; then
  mkdir -p "$BACKUP_DIR"
  echo
  echo "Backing up live application..."
  /usr/bin/ditto "$TARGET" "$BACKUP_DIR/PlexCurator"
  echo "Application backup: $BACKUP_DIR/PlexCurator"

  if [[ -x "$TARGET/plex-curator" ]]; then
    echo "Creating state/config safety backup..."
    "$TARGET/plex-curator" backup --reason "pre-deploy-$STAMP" ||       echo "WARNING: existing Curator backup command failed; application backup still exists." >&2
  fi
fi

NEED_SUDO=0
PARENT="$(dirname "$TARGET")"
if [[ -e "$TARGET" ]]; then
  [[ -w "$TARGET" ]] || NEED_SUDO=1
else
  [[ -w "$PARENT" ]] || NEED_SUDO=1
fi

if [[ "$NEED_SUDO" -eq 1 ]]; then
  echo "Administrator permission is required to update $TARGET"
  sudo mkdir -p "$TARGET"
  sudo chown -R "$(id -un):$(id -gn)" "$TARGET"
else
  mkdir -p "$TARGET"
fi

echo
echo "Deploying backend source..."
/usr/bin/rsync -a --delete   --exclude '.venv/'   --exclude '__pycache__/'   --exclude '*.pyc'   --exclude '.DS_Store'   "$SOURCE/" "$TARGET/"

chmod +x   "$TARGET/install.sh"   "$TARGET/plex-curator"   "$TARGET/plex-curator-api"   "$TARGET/launchd-manager.py"

echo
echo "Installing Python dependencies..."
"$TARGET/install.sh"

if [[ -f "$CONFIG_DIR/.env" ]]; then
  echo
  echo "Running post-deploy Doctor..."
  "$TARGET/plex-curator" doctor
else
  echo
  echo "No $CONFIG_DIR/.env found."
  echo "Backend files are installed; run:"
  echo "  cd \"$TARGET\""
  echo "  ./plex-curator setup"
fi

API_PLIST="$HOME/Library/LaunchAgents/com.ry.plexcurator.api.plist"
if [[ "$RESTART_API" -eq 1 && -f "$API_PLIST" ]]; then
  echo
  echo "Reloading localhost API LaunchAgent..."
  "$TARGET/.venv/bin/python" "$TARGET/launchd-manager.py" install api-server
  sleep 1
  "$TARGET/plex-curator-api" ping || {
    echo "WARNING: API did not answer immediately. Check:" >&2
    echo "  $TARGET/plex-curator logs api-server --errors" >&2
  }
fi

echo
echo "Backend deployment complete."
if [[ -d "$BACKUP_DIR" ]]; then
  echo "Pre-deploy backup: $BACKUP_DIR"
fi
