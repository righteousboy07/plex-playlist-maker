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

backend_args=()
mac_args=()
[[ "$DRY_RUN" -eq 1 ]] && backend_args+=(--dry-run) && mac_args+=(--dry-run)
[[ "$NO_OPEN" -eq 1 ]] && mac_args+=(--no-open)

"$ROOT/scripts/install-backend.sh" "${backend_args[@]}"
"$ROOT/scripts/install-macos-app.sh" "${mac_args[@]}"
