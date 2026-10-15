#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=0
NO_OPEN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --no-open) NO_OPEN=1; shift ;;
    -h|--help)
      echo "Usage: ./scripts/install-all.sh [--dry-run] [--no-open]"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  bash "$ROOT/scripts/install-backend.sh" --dry-run
else
  bash "$ROOT/scripts/install-backend.sh"
fi

if [[ "$DRY_RUN" -eq 1 && "$NO_OPEN" -eq 1 ]]; then
  bash "$ROOT/scripts/install-macos-app.sh" --dry-run --no-open
elif [[ "$DRY_RUN" -eq 1 ]]; then
  bash "$ROOT/scripts/install-macos-app.sh" --dry-run
elif [[ "$NO_OPEN" -eq 1 ]]; then
  bash "$ROOT/scripts/install-macos-app.sh" --no-open
else
  bash "$ROOT/scripts/install-macos-app.sh"
fi
