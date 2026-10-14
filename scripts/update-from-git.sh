#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Refusing to update: repository has uncommitted changes." >&2
  echo "Commit, stash, or discard them first." >&2
  exit 1
fi

BRANCH="$(git branch --show-current)"
if [[ -z "$BRANCH" ]]; then
  echo "Detached HEAD; switch to a branch before updating." >&2
  exit 1
fi

echo "Updating branch: $BRANCH"
git pull --ff-only

"$ROOT/scripts/install-all.sh" "$@"
